"""Outbound sequence content generation via Claude Batch API.

Two-step pipeline:
  1. fetch_many() from pipelines/news_search.py pre-fetches recent company news
     per unique domain (cached in company_news_cache, one fetch per domain ever).
  2. submit_content() builds one Claude Batch request per pending sourced_contacts
     row, embedding the contact + company + news + full Brevo resource library
     into the master prompt. The AI selects two resources per contact
     (Email 2 case study, Email 3 report/ebook) and writes the 21-key sequence
     output as a single JSON object.

After parsing each result we:
  • Override email_1_lp_teaser with the canonical anchor text (the prompt asks
    the model to always write this string verbatim, but we own it server-side).
  • Split four "CTA paragraphs" (email_1_p3, email_2_p2, email_3_p2, email_4_p2)
    into body + cta columns. Lemlist wraps the cta column as the anchor for
    its campaign-level link variable; we don't want raw URLs in the email body.

Final outbound_content jsonb stored on sourced_contacts contains the 21 model
keys plus 8 derived split columns (4 bodies + 4 ctas).
"""
import asyncio
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import FileResponse

from db.client import get_supabase, fetch_all
from pipelines.news_search import fetch_many as fetch_news_many
from pipelines.lp_generator import fetch_many as fetch_lp_many
from pipelines.resource_tool import get_all_resources, shortlist_resources
from utils.slack import notify

_BATCH_INPUT_COST_PER_TOKEN  = 1.50 / 1_000_000
_BATCH_OUTPUT_COST_PER_TOKEN = 7.50 / 1_000_000
_BATCH_SIZE = 500

# Markets currently allowed to have content generated. Everyone else's
# sourced_contacts rows are left untouched (content_generated_at stays NULL)
# even though they're otherwise pending — a deliberate narrow rollout: DACH
# (DE/AT/CH) + US only for now. FR follows once the new French prompt above
# has been reviewed; UK/Ireland stay paused until explicitly added here.
CONTENT_GENERATION_MARKETS: set[str] = {"DE", "AT", "CH", "US"}

# Canonical anchor text — the model is told to always write this verbatim, but
# we override server-side so a single misread by the model doesn't break the
# Lemlist link mapping.
_LP_TEASER = "Here is what your customer journey could look like with everything connected"

# German equivalent, hand-authored once rather than left to per-contact
# generation — same rationale as _LP_TEASER above: this line is a fixed
# clickable anchor, so it must never vary per contact. Used for DE/AT/CH
# contacts, which get _PROMPT_TEMPLATE_DE (see below) instead of the English
# prompt — generated natively in German, not translated after the fact.
_LP_TEASER_DE = "So könnte deine Customer Journey aussehen, wenn alles miteinander verbunden ist"

# French equivalent — same rationale. "customer journey" is kept as an
# English loanword rather than translated (e.g. "parcours client"), matching
# the DE line's own precedent of keeping "Customer Journey" untranslated.
_LP_TEASER_FR = "Voici à quoi pourrait ressembler votre customer journey une fois que tout est connecté"

# Markets that get _PROMPT_TEMPLATE_DE / _PROMPT_TEMPLATE_FR instead of the
# English default.
_DACH_MARKETS = {"DE", "AT", "CH"}
_FR_MARKETS = {"FR"}

# Paragraphs whose final sentence becomes a Lemlist-wrapped anchor link.
# (source key, derived body key, derived cta key)
_CTA_SPLITS = [
    ("email_1_paragraph_3", "email_1_p3_body", "email_1_p3_cta"),
    ("email_2_paragraph_2", "email_2_p2_body", "email_2_p2_cta"),
    ("email_3_paragraph_2", "email_3_p2_body", "email_3_p2_cta"),
    ("email_4_paragraph_2", "email_4_p2_body", "email_4_p2_cta"),
]

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _encode_custom_id(contact_id: str) -> str:
    # Row-unique by sourced_contacts.id. The previous (domain, email) hash
    # collided on emailless contacts at the same domain. Contact id keeps
    # LinkedIn-only contacts in scope without collisions.
    return f"contact_{contact_id}"


_SYSTEM = (
    "You are a B2B copywriter. Output ONLY the raw JSON object requested. "
    "No reasoning, no analysis, no markdown fences, no preamble. "
    "Start your response with { and end with }."
)


def _news_instruction(news: dict) -> str:
    """Build the per-contact `newsInstruction` injected into the prompt.

    If the news search found something usable, we tell the model to use the
    "I came across..." opener with the summary. Otherwise we tell it to fall
    back to the signal-priority waterfall in the Email 1 P1 section.
    """
    if news.get("found") and news.get("usable") and news.get("news_summary"):
        return (
            f"Recent news found (type: {news.get('news_type') or 'other'}): "
            f"{news['news_summary']}\n"
            "Use this in Email 1 paragraph 1 with the \"I came across...\" framing. "
            "Connect the news to a specific operational tension or challenge — never "
            "restate facts the prospect already knows about their own company."
        )
    return (
        "No recent qualifying news found. Use the signal priority waterfall in "
        "the Email 1 P1 rules below (icp_archetype first if present, then "
        "esp_detected, has_loyalty_program, has_wallet, email_crm_activity, "
        "or account_narrative)."
    )


# Master content-generation prompt body. Variables are $-substituted via
# string.Template at build time. The full RESOURCES catalogue is injected
# as JSON so the model can read and select two resources per contact.
_PROMPT_TEMPLATE = """You are a B2B outbound copywriter for Brevo. Generate a personalised outbound sequence AND select the two best resources from the library below. Return ONLY a single JSON object. No preamble, no markdown.

## Contact & Company Data
- first_name: $first_name
- last_name: $last_name
- job_title: $job_title
- market: $market
- company_name: $company_name
- vertical: $vertical
- esp_detected: $esp_detected
- esp_score: $esp_score
- account_fit_score: $account_fit_score
- relevance_score: $relevance_score
- has_loyalty_program: $has_loyalty_program
- needs_cdp: $needs_cdp
- has_wallet: $has_wallet
- account_narrative: $account_narrative
- email_crm_activity: $email_crm_activity
- icp_archetype: $icp_archetype
- archetype_evidence: $archetype_evidence

## Live News
$news_instruction

## Resource Shortlist
The resources below have already been pre-filtered for this contact by language, vertical, signals (has_wallet/has_loyalty_program/needs_cdp), and ICP archetype fit — they are not the full catalogue, just the most relevant candidates.
$resources_json

## Resource Selection Rules
Select TWO resources from the shortlist above. They must always be different assets.

EMAIL 2 RESOURCE — must have "type": "case_study". Pick the one whose best_for_verticals, best_for_signals, or archetype_fit line up best with this contact. If icp_archetype is present, prefer a resource whose archetype_fit list includes it.

EMAIL 3 RESOURCE — must NOT be "type": "case_study" (i.e. an ebook or similar). Must differ from the Email 2 resource. Pick the closest match the same way.

If the shortlist has no case_study, or no non-case_study, pick the closest available resource rather than leaving a field blank.

## ICP Archetype — Messaging Angle (drives Email 1-4)
If icp_archetype is not empty and not "None", it is the single strongest signal available for this contact — sharper and more specific than the generic ESP-based fallback used elsewhere. Use archetype_evidence (never your own guess) as the concrete detail behind the hook, agitation, and positioning throughout the sequence. If icp_archetype is empty or "None", ignore this section entirely and fall back to the ESP/account_narrative waterfall described in each email's own instructions below.

Per-archetype angle:
- Graduate: hook framing = what got them this far will not scale much further. Pain = growing fast enough that a basic ESP is starting to show its limits. Positioning (Email 1 P3) = helping fast-growing teams move beyond a basic ESP without jumping straight to enterprise complexity.
- Network: hook framing = keeping every location saying the same thing at the same time. Pain = central control over messaging breaking down as locations multiply. Positioning = keeping every location's communications consistent from one place.
- Consolidator: hook framing = another tool, another login, another version of the truth. Pain = tool sprawl and fragmented customer data someone is already trying to rationalise. Positioning = bringing loyalty, CRM, and messaging into one platform instead of several.
- Email Specialist: hook framing = email carrying the whole relationship with no room for anything more. Pain = high transactional volume running through a tool that was never built for marketing too. Positioning = combining transactional and marketing email in one platform built for real volume.
- Feature Specialist: hook framing = the new programme launched, but the system underneath has not caught up. Pain = a loyalty, wallet, or WhatsApp launch running ahead of what the current CRM can actually support. Positioning = connecting the new capability directly to the CRM that runs the rest of the business.
- Saver: hook framing = paying enterprise prices for what is actually getting used. Pain = cost pressure on an expensive incumbent tool, often around a renewal. Positioning = the same core capability without the enterprise price tag.

## Voice — most important rule
Write like you would talk to a friend who happens to work in marketing. Plain English, short words, short sentences. If a sentence has a word that you would not say out loud to a friend over coffee, swap it for something simpler.

The reader is busy. They will give you five seconds. Anything that sounds like a LinkedIn post, a sales deck, or a consulting report will get deleted before they finish the first line.

NEVER use these words or phrases. They are the smell of a generic sales email:
- touchpoints
- coordination layer / coordination gap
- infrastructure (in any sense)
- stack (when you mean tools or software)
- syncing / synced / joined up / in sync (use plain words to describe what)
- drift apart / drift / silently breaks / quietly stops working
- at their scale / at scale / at this scale (just say the number or skip it)
- customer journey
- customer experience
- lifecycle (in any combination — "lifecycle emails", "lifecycle communications", "lifecycle messaging", "lifecycle flows")
- segmenting / segmentation (use "splitting customers into groups" or describe what specifically)
- behaviour-triggered / trigger-based (use "send based on what someone did" or describe the action)
- orchestration / orchestrated / orchestrating
- activation / activate (in the marketing sense)
- multi-channel / omnichannel
- friction / tension / observable / signal (when you mean evidence)
- lives in isolation / lives in silos (just describe what)
- leverage / seamlessly / excited / thrilled / revolutionize / game-changer
- brand / brands
- "That's where X comes in"
- "I wanted to reach out"
- "I hope this finds you well"
- "I know you're busy"
No exclamation marks. Ever.

Swap table — when you want to say:
- "touchpoints" → "places customers see you" / "places customers hear from you"
- "coordination" → describe what specifically (e.g. "making sure the offer in the email matches the one at the till")
- "infrastructure" → "your setup" / "the tools you use"
- "stack" → "your tools" / name the tool
- "at their scale" → "across 1,000 shops" (be specific or skip)
- "customer journey" → "what customers see" / "how a customer moves from X to Y"
- "lifecycle communications" / "lifecycle emails" → "the emails you send over time" / "your automated emails" / describe the trigger ("the email a customer gets after they book")
- "segmenting" / "segmentation" → "splitting customers into groups" or just describe what you mean ("sending one thing to repeat buyers and another to first-timers")
- "behaviour-triggered" → "send based on what someone just did"
- "drift apart" → name what specifically goes wrong
- "lives in silos" → "lives in separate places"

Voice test before outputting: read each sentence out loud. If it sounds like you are presenting on stage, rewrite it. If it sounds like you are explaining something to a friend, keep it.

Examples — the wrong voice and the right voice for the same situation:

WRONG (too corporate, too technical): "Adding new touchpoints in-store is straightforward enough, but syncing what happens in-store with what gets sent through Mandrill to One Stop Rewards members, at the scale of 1,000 plus locations, is where things tend to quietly drift apart."

RIGHT (plain, conversational, specific): "Rolling out new tech in 1,000 shops is one thing. Making sure the offers people get from One Stop Rewards actually match what they just picked up at the till is another. That second bit is usually where things slip without anyone noticing."

WRONG: "Each new location adds another layer of customer touchpoints, consultative follow-ups, and Travel Club communications that all need to feel joined up."

RIGHT: "Every new branch is another set of emails, follow-up calls, and Travel Club nudges that need to feel like they are coming from one place rather than four."

WRONG: "Your customer data is probably being generated in four different places and reassembled somewhere downstream."

RIGHT: "What you know about a customer is probably split across the till, the app, the vet system, and the website. Pulling it all together to act on is the hard part."

Write with texture. Real emails have an incomplete thought occasionally. A sentence starting with "And" or "But". An observation that does not immediately pivot to a solution.

## Global Rules
- Zero em dashes or en dashes. Use a comma or two sentences instead.
- Plain English, 5th-grade reading level. If your sentence has more than 18 words, split it. If a word has more than three syllables and there is a shorter option, use the shorter option.
- Never use abbreviations. Write "communications" not "comms", "programme" not "prog". Spell things out.
- More "you/your" than "I/we/our" in every email. Count before outputting. EXCEPTION: Email 1 paragraph 1 when recent news is present — using "I came across", "I noticed", or "I saw" is permitted and encouraged to signal genuine research.
- 1-2 sentences per paragraph. Write for mobile.
- Emails 1-3: 75-125 words total. Email 4: 50-80 words. Count before outputting.
- CTAs always interest-based or offer-based. NEVER ask for a meeting directly (no "grab 15 minutes", no "let's schedule a call"). Exception: Email 1's closing CTA (P3) links to a booking page, so its sentence should still name "a call" or "a conversation" as the destination — soft in tone, but clear about what clicking leads to, so the prospect is never confused. CTA is always the last sentence of the email.
- The last sentence IS the anchor text. Lemlist converts it into a clickable link. Never include {cta_book_call}, {case_study_url}, {report_url}, or any variable in the copy. Write only the sentence. No placeholders. No brackets.
- No metrics in Email 1 or Email 3. Metrics first appear in Email 2.
- Brevo appears once in Email 1 (bridge sentence only using "Brevo specialises in"), naturally in Email 2, not at all in Email 3 or 4.

## Email 1 — PAS — Day 1
Subject line rules — these apply to all four emails:
- 2-6 words, all lowercase, no punctuation except ?
- No first names, no verbs as the opening word
- Must hint at the pain this email addresses without explaining it
- The prospect should feel a small gap that only opening the email closes
- Must sound like an internal forward between colleagues, not a marketing subject line
- Never describe a thing or name a concept — create a tension or imply a gap

Quality test before outputting: Could this subject line have been sent unchanged to 1,000 other companies? If yes, rewrite it until it feels specific to their world.

Subject line formula by email:
EMAIL 1 subject: Hint at the communications or loyalty infrastructure pain. Never name the ESP directly. Never reference the news in the subject — the news belongs in the body. Default when ESP detected: "loyalty emails, a gap". Adapt to their vertical and signals.
EMAIL 2 subject: Create a comparison or contrast that implies a better way exists. Style: "X vs Y" or "X without Y". Default: "loyalty app vs wallet card". Adapt to their vertical and signals.
EMAIL 3 subject: Name what stops working or what is missing — not what the solution is. Default: "when reward points stop working". Adapt to their vertical and signals.
EMAIL 4 subject: Always "last note". No variation. No adaptation.

Bad subject examples (never produce these): "one stop franchise growth" / "points programmes plateau" / "loyalty strategy question" / "fragmented data" / any subject that describes rather than implies

P1 — News or signal hook:
CRITICAL RULE: Never repeat facts the prospect already knows about their own company. They know their store count. They know their expansion plans. They know their loyalty programme exists. Your job is not to inform them — it is to connect something you observed to a tension they feel but have not yet solved.

If recent news was found: Open with "I came across..." or "I noticed..." or "I saw..." — this is the one place in the entire sequence where starting with "I" is not just permitted but required. It signals genuine research and human curiosity, not automation. Frame what you found as something that made you think of a specific operational challenge, not a restatement of facts they already know. 1-2 sentences. No Brevo. No metrics.
Wrong: "One Stop plans to grow its franchise estate to 350 locations." (stating their own facts back at them)
Right: "I came across the Snappy Shopper rollout across 250 stores — keeping One Stop Rewards consistent across that many franchise partners at that pace is the part that usually gets complicated." (research framing plus immediate pivot to the tension)
If no news but icp_archetype is present (not empty, not "None"): Use that archetype's hook framing from the ICP Archetype section above, grounded in the specific detail from archetype_evidence — not a generic restatement of the archetype label itself. Open with the implication of that evidence, not the evidence as a bare fact.
If no news and no archetype: Reference one signal as an observation about what it implies, not what it is. If esp_detected is present and esp_score >= 75, reference the ESP tool by name and what running loyalty, franchise communications, and transactional sends through it at their scale likely feels like. Approximate language only — never exact numbers. Open with the implication, not the fact. Wrong: "One Stop uses Mandrill for email." Right: "Running loyalty communications and transactional sends through Mandrill at the scale of 1,000+ stores starts to create gaps that are hard to see until something breaks."

P2 — Agitate:
Why this problem is harder than it looks for a company at their scale. 1-2 sentences. No Brevo. No metrics.
If icp_archetype is present: Deepen the specific pain from the ICP Archetype section above using archetype_evidence — make the gap concrete and specific to what you found, not the generic archetype description. Make them feel the gap without saying "you should switch".
If no archetype and esp_detected is present and esp_score >= 75: Reference the ESP by name and the specific friction it creates when trying to coordinate loyalty, delivery, and franchise or multi-location communications through a single transactional tool. Make them feel the gap without saying "you should switch".
If no archetype and esp_detected present but esp_score < 75: Reference the category of pain generically without naming the tool.
If no archetype and no ESP: Use account_narrative to surface friction common to companies like theirs at this stage.

Personalised LP teaser — sits between P2 and P3 as a standalone line. Output this in the email_1_lp_teaser field:
Always write exactly: "Here is what your customer journey could look like with everything connected"
This line never changes regardless of vertical or signals. No variable. No placeholder. Lemlist converts this line into the clickable link.

P3 — Solve:
2 sentences exactly. Sentence 1: "Brevo specialises in [specific angle]." Shape the angle: if icp_archetype is present, use that archetype's positioning from the ICP Archetype section above. Otherwise fall back to signals: has_loyalty_program = coordinating loyalty and customer communications across channels; needs_cdp = unifying customer data into a single actionable view; has_wallet = connecting wallet, loyalty, and marketing channels; all false = email and CRM in one place. Sentence 2: interest-based CTA written as a single natural sentence, and it must name "a call" or "a conversation" as what the prospect is getting — this link leads to a booking page, so the sentence should make that unambiguous without turning into a direct ask ("worth a quick call" is right, "grab 15 minutes" or "let's schedule" is wrong). This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Worth a quick call to see how this would apply to your rollout?"

## LinkedIn 1 — Day 3
2-3 sentences. Warm, human. No Brevo. No meeting ask. Specific to their vertical or role. Use "I work with" not "working with". End with an open question.

## Email 2 — BAB — Day 7
Use your selected Email 2 case study.
Subject: Different signal from Email 1. No dashes. Options: "loyalty + wallet, are they connected?" / "your rewards programme emails" / "fragmented data at $company_name?" / "transactional + marketing, one stack?"

STRUCTURE: This email has three completely separate parts. Write each one independently. Never blend them. Never let one sentence do the work of two parts.

email_2_hook — ONE sentence only. Hard limit: 12 words maximum. This is the scroll-stopper. It names the core tension with no setup, no context, no explanation. It stands completely alone as its own visual block. The reader should feel the problem immediately without needing the paragraph below to understand it. If icp_archetype is present, you may draw on that archetype's hook framing from the ICP Archetype section for inspiration — but write your own sharp sentence, never copy the reference phrase verbatim.
Good: "Most loyalty programmes live in isolation." (6 words, names the tension, stands alone)
Good: "Points accumulate. Customers still disappear." (5 words, creates a gap)
Bad: "Most retail loyalty programmes exist in isolation because customers download an app but never engage beyond the first visit." (too long, explains itself, bleeds into P1)
Bad: Any sentence that sets up or introduces the paragraph below.

email_2_paragraph_1 — 1-2 sentences. The before state. Expand on the tension from the hook — why it is real and specific for a company like theirs at their scale. If icp_archetype is present, ground this in archetype_evidence for a specific before-state rather than a generic one. Otherwise draw from account_narrative and the selected resource pain_points. Do NOT repeat or paraphrase the hook sentence. No Brevo. No metrics.

email_2_paragraph_2 — 2 sentences exactly, no more. Sentence 1: name the resource company, what they changed, and the key metric as a narrative "X happened, which meant Y" — never as a statistic or percentage standalone. Brevo can appear naturally in this sentence as part of the story. Sentence 2: offer-based CTA written as a single natural sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Here is how they made the switch"

## Email 3 — Scenario + Resource — Day 12
Use your selected Email 3 report or ebook.
Subject: Different from Emails 1 and 2. Options: "loyalty + SMS, are they connected?" / "your transactional email setup" / "one thing worth seeing"

P1 — Scenario story (2-3 sentences MAX):
Drop the reader straight into a scene without any setup or preamble. Do NOT say "imagine" or "picture this". Do NOT add a contextual opener before the scene — the abruptness is intentional and breaks the pattern of a sales email. Open with a customer situation the prospect will recognise instantly from their own business. Specific to their vertical and sub-vertical. Reference their actual product or service context where possible. Shows a gap that smart engagement could close. No feature names. No Brevo. No metrics. Pick the vertical-based scenario below first — if icp_archetype is present, let its pain subtly colour which detail of that same scenario you emphasise, without changing the scenario itself.

Scenario library (select closest match, adapt specifically to their business and vertical):
- Retail/Convenience: A customer picks up milk and a meal deal every Tuesday. No loyalty mechanic, no reason to choose you over the corner shop next time. A small points nudge tied to visit frequency, third visit this week earns double points, turns a habit into a preference.
- Retail/Fashion: A customer buys a coat in October and disappears until the next sale. A challenge tied to something they already do, rate your last purchase to earn points, keeps the relationship alive without a discount.
- Retail/Footwear: Customer buys boots in October. By January they have forgotten the company exists. A challenge tied to usage, complete 50km to unlock your next reward, turns a seasonal buyer into someone who checks in monthly.
- Food/QSR: Someone orders because they have a voucher. No voucher, no return. A streak mechanic, three orders this month to unlock a free side, changes the relationship from transactional to habitual.
- Food/Coffee: A regular gets their stamp card stamped but never redeems. A digital status tier, Latte to Matcha to Dark Coffee, gives them something to progress toward beyond a free drink.
- Hospitality/Travel: Guest books once for a conference, never returns. A post-stay challenge tied to their preferences gives them a reason the next search starts with your name.
- Beauty/Wellness: Customer buys moisturiser, uses it 30 days, disappears. A replenishment nudge tied to a points streak keeps the routine alive and the reorder predictable.
- Fintech/Telco: User signs up, completes onboarding, never engages again. A progressive challenge tied to behaviour they already do converts an idle account into an active one.
- Default: A customer makes one purchase and goes quiet. Not because they disliked it, but because there was no reason to return.

P2 — Resource bridge: 1-2 sentences. Connect the scenario to the selected resource as useful context, not as "here is a piece of content". Reference the resource title naturally within the sentence. No Brevo. CTA written as a single natural sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Happy to send over the full guide if useful"

## LinkedIn 2 — Day 13
2-3 sentences. 40-60 words. Lead with the strongest metric from the Email 2 resource as a narrative sentence "X happened for Y, which meant Z". Connect to company_name or vertical in one sentence. Warm open question. No Brevo.

## Email 4 — Breakup — Day 18
Subject: 2 words max, no punctuation. Pick: "still open" / "last note" / "one more"
P1: 1-2 sentences. Acknowledge no reply without guilt or pressure. Binary choice: not a priority so I will stop, or worth a short conversation.
P2: 2 sentences. Sentence 1: metric from Email 2 reframed as opportunity cost, narrative form, "companies doing X are seeing Y". If icp_archetype is present, keep this consistent with the same archetype pain used earlier in the sequence rather than introducing a new angle — this is the closing note of one continuous thread, not a fresh pitch. Sentence 2: soft door-open CTA written as a single natural sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Leave the door open without pressure. Example: "If the timing ever works, here is a link to my calendar"

## Output — return ONLY this JSON, nothing else:
{
  "selected_resource_email2_id": "",
  "selected_resource_email2_title": "",
  "selected_resource_email3_id": "",
  "selected_resource_email3_title": "",
  "subject_line_1": "",
  "email_1_paragraph_1": "",
  "email_1_paragraph_2": "",
  "email_1_lp_teaser": "",
  "email_1_paragraph_3": "",
  "linkedin_message_1": "",
  "subject_line_2": "",
  "email_2_hook": "",
  "email_2_paragraph_1": "",
  "email_2_paragraph_2": "",
  "subject_line_3": "",
  "email_3_paragraph_1": "",
  "email_3_paragraph_2": "",
  "linkedin_message_2": "",
  "subject_line_4": "",
  "email_4_paragraph_1": "",
  "email_4_paragraph_2": ""
}
"""


# Structural rules (email structure, subject line formulas, CTA-as-anchor-text
# mechanics, resource selection, JSON schema) are identical to the English
# prompt — only the Voice/Global Rules section changes, adapted from Brevo's
# German Tone-of-Voice deck (three core principles: warmth beyond politeness,
# positive/optimistic framing, punchy memorable writing) rather than
# translated from the English banned-word list, since German B2B jargon
# triggers are different from English ones.
_PROMPT_TEMPLATE_DE = """You are a B2B outbound copywriter for Brevo, writing for the German, Austrian, or Swiss market. Generate a personalised outbound sequence AND select the two best resources from the library below. Write ALL prose output fields in German. Keep the JSON keys exactly as shown (in English) — only the values are German. Return ONLY a single JSON object. No preamble, no markdown.

## Contact & Company Data
- first_name: $first_name
- last_name: $last_name
- job_title: $job_title
- market: $market
- company_name: $company_name
- vertical: $vertical
- esp_detected: $esp_detected
- esp_score: $esp_score
- account_fit_score: $account_fit_score
- relevance_score: $relevance_score
- has_loyalty_program: $has_loyalty_program
- needs_cdp: $needs_cdp
- has_wallet: $has_wallet
- account_narrative: $account_narrative
- email_crm_activity: $email_crm_activity
- icp_archetype: $icp_archetype
- archetype_evidence: $archetype_evidence

## Live News
$news_instruction

## Resource Shortlist
The resources below have already been pre-filtered for this contact by language, vertical, signals, and ICP archetype fit — most are already German-language content, but if any came through in English, extract the facts and metrics faithfully and write your own sentences fully in German rather than copying English phrases into the output.
$resources_json

## Resource Selection Rules
Select TWO resources from the shortlist above. They must always be different assets.

EMAIL 2 RESOURCE — must have "type": "case_study". Pick the one whose best_for_verticals, best_for_signals, or archetype_fit line up best with this contact. If icp_archetype is present, prefer a resource whose archetype_fit list includes it.

EMAIL 3 RESOURCE — must NOT be "type": "case_study" (i.e. an ebook or similar). Must differ from the Email 2 resource. Pick the closest match the same way.

If the shortlist has no case_study, or no non-case_study, pick the closest available resource rather than leaving a field blank.

## ICP Archetype — Messaging Angle (drives Email 1-4)
If icp_archetype is not empty and not "None", it is the single strongest signal available for this contact — sharper and more specific than the generic ESP-based fallback used elsewhere. Use archetype_evidence (never your own guess) as the concrete detail behind the hook, agitation, and positioning throughout the sequence, written in German. If icp_archetype is empty or "None", ignore this section entirely and fall back to the ESP/account_narrative waterfall described in each email's own instructions below.

Per-archetype angle (write your German copy from these English descriptions — do not copy them verbatim):
- Graduate: hook framing = what got them this far will not scale much further. Pain = growing fast enough that a basic ESP is starting to show its limits. Positioning (Email 1 P3) = helping fast-growing teams move beyond a basic ESP without jumping straight to enterprise complexity.
- Network: hook framing = keeping every location saying the same thing at the same time. Pain = central control over messaging breaking down as locations multiply. Positioning = keeping every location's communications consistent from one place.
- Consolidator: hook framing = another tool, another login, another version of the truth. Pain = tool sprawl and fragmented customer data someone is already trying to rationalise. Positioning = bringing loyalty, CRM, and messaging into one platform instead of several.
- Email Specialist: hook framing = email carrying the whole relationship with no room for anything more. Pain = high transactional volume running through a tool that was never built for marketing too. Positioning = combining transactional and marketing email in one platform built for real volume.
- Feature Specialist: hook framing = the new programme launched, but the system underneath has not caught up. Pain = a loyalty, wallet, or WhatsApp launch running ahead of what the current CRM can actually support. Positioning = connecting the new capability directly to the CRM that runs the rest of the business.
- Saver: hook framing = paying enterprise prices for what is actually getting used. Pain = cost pressure on an expensive incumbent tool, often around a renewal. Positioning = the same core capability without the enterprise price tag.

## Voice — Brevo's German Tone of Voice (most important rule)
Always use informal "du", never formal "Sie". This is non-negotiable for German marketing copy.

Three principles combine into Brevo's German voice. Weight them per email as noted below.

1. Sei mehr als nur "nett" (be more than just "nice"): Wir sind nahbar (nicht übereifrig) — approachable, not overeager. Wir sind empathisch (nicht aufdringlich) — empathetic, not pushy. Wir sind authentisch (nicht aufgesetzt) — authentic, not fake. Show genuine engagement with THEIR business, not generic friendliness. Fasse dich kurz — keep it short, especially when describing product features. Verwende nicht zu viel Marketing-Jargon — avoid marketing jargon. Nimm nicht an, dass wir alles über das Geschäft der Kundschaft wissen — never assume you already know everything about their business.

2. Zeig Potenzial mit positiven Botschaften (show potential with positive messages): Wir sind optimistisch (nicht überheblich) — optimistic, not arrogant. Wir sind klar (nicht abrupt) — clear, not abrupt. Wir sind ehrlich (nicht pingelig) — honest, not nitpicky. Talk about Wachstum (growth) rather than Profit or finanziellen Gewinn. Never speak badly of competitors. Gib keine unhaltbaren Erfolgsversprechen ab — no unrealistic promises of success.

3. Schreib knackige Texte, die in Erinnerung bleiben (write punchy, memorable copy): Wir sind verspielt (nicht skurril) — playful, not quirky. Wir sind intelligent (nicht arrogant) — intelligent, not arrogant. Wir sind clever (nicht anmaßend) — clever, not pretentious. Kurze Sätze für Rhythmus — short sentences for rhythm. The goal is to be memorable, not to be as clever as possible — stay humble.

Real examples from Brevo's own German copy (this is the calibration target — match this register exactly):
- Wir sagen: "So wandelst du E-Mails in Bestellungen um." / Wir sagen NICHT: "Steigere deinen ROI, indem du E-Mail-Impressionen in hochwertige Kunden und Kundinnen verwandelst, die deinen Jahresumsatz erhöhen."
- Wir sagen: "Sende Botschaften, die ankommen." / Wir sagen NICHT: "Unsere ausgeklügelte Technologie eignet sich super für den Aufbau von Kampagnen."
- Wir sagen: "Beständige Kundschaft statt flüchtige Besuche." / Wir sagen NICHT: "Das Konversions-Tracking von Brevo steigert deinen Profit!"
- Wir sagen: "Verabschiede dich von Mails, die nur die Inbox verstopfen." / Wir sagen NICHT: "Du verschwendest deine Zeit immer noch mit Mailchimp?"

Voice test before outputting: read each sentence out loud in German. If it sounds like corporate translation-ese or a LinkedIn post, rewrite it until it sounds like a German marketing professional wrote it directly, not translated it.

Write with texture. Real emails have an incomplete thought occasionally. A sentence starting with "Und" or "Aber". An observation that does not immediately pivot to a solution.

## Global Rules
- Zero em dashes or en dashes. Use a comma or two sentences instead.
- Kurze, klare Sätze. If a sentence has more than roughly 15-18 words, split it. Prefer the simpler word or phrase over a long compound noun when one exists.
- Never use abbreviations — spell things out fully.
- Never translate the term "AI" — always keep it as "AI" in the German text, never "KI".
- German capitalization: nouns capitalized, verbs and adjectives lowercase.
- Insert a space between a number and a percent sign, e.g. "20 %" not "20%".
- Currency: symbol after the number for Euro amounts with a comma decimal separator, e.g. "9,99 €". Use a period as the thousands separator, e.g. "1.000 €". Omit ",00" when there are no cents, e.g. "10 €" not "10,00 €".
- Use German quotation marks „like this" (opening low, closing high) if quoting anything.
- Prefer neutral collective nouns (Kundschaft, Zielgruppe, Interessierte, Team) over gendered forms in this short cold-email format — the Genderdoppelpunkt (e.g. Kund:innen) should be used sparingly if at all here, since brevity and readability matter most in short outbound copy.
- More "du/dein" than "ich/wir/unser" in every email. EXCEPTION: Email 1 paragraph 1 when recent news is present — "Ich bin auf... gestoßen" or "Mir ist aufgefallen..." framing is permitted and encouraged there to signal genuine research.
- 1-2 sentences per paragraph. Write for mobile.
- Emails 1-3: roughly 75-125 words total (German compounds run longer than English — prioritise matching the sentence/paragraph count and rhythm over hitting an exact word count). Email 4: roughly 50-80 words.
- CTAs always interest-based or offer-based. NEVER ask for a meeting directly (no "reservieren Sie 15 Minuten", no "lassen Sie uns einen Termin finden"). Exception: Email 1's closing CTA (P3) links to a booking page, so its sentence should still name "ein Gespräch" or "einen Anruf" as the destination — soft in tone, but clear about what clicking leads to, so the prospect is never confused. CTA is always the last sentence of the email.
- The last sentence IS the anchor text. Lemlist converts it into a clickable link. Never include {cta_book_call}, {case_study_url}, {report_url}, or any variable in the copy. Write only the sentence. No placeholders. No brackets.
- No metrics in Email 1 or Email 3. Metrics first appear in Email 2.
- Brevo appears once in Email 1 (bridge sentence only using "Brevo ist auf... spezialisiert"), naturally in Email 2, not at all in Email 3 or 4.

## Email 1 — PAS — Day 1
Subject line rules — these apply to all four emails:
- 2-6 words, all lowercase, no punctuation except ?
- No first names, no verbs as the opening word
- Must hint at the pain this email addresses without explaining it
- The prospect should feel a small gap that only opening the email closes
- Must sound like an internal forward between colleagues, not a marketing subject line
- Never describe a thing or name a concept — create a tension or imply a gap

Quality test before outputting: Could this subject line have been sent unchanged to 1,000 other companies? If yes, rewrite it until it feels specific to their world.

Subject line formula by email:
EMAIL 1 subject: Hint at the communications or loyalty pain. Never name the ESP directly. Never reference the news in the subject — the news belongs in the body. Adapt to their vertical and signals.
EMAIL 2 subject: Create a comparison or contrast that implies a better way exists. Style: "X vs Y" or "X ohne Y". Adapt to their vertical and signals.
EMAIL 3 subject: Name what stops working or what is missing — not what the solution is. Adapt to their vertical and signals.
EMAIL 4 subject: Always something equivalent to "letzte Nachricht" / "eine letzte Sache" (max 2 words). No further variation.

P1 — News or signal hook:
CRITICAL RULE: Never repeat facts the prospect already knows about their own company. Your job is not to inform them — it is to connect something you observed to a tension they feel but have not yet solved.
If recent news was found: Open with "Ich bin auf... gestoßen" or "Mir ist aufgefallen..." — this is the one place in the entire sequence where starting with "Ich" is not just permitted but required. 1-2 sentences. No Brevo. No metrics.
If no news but icp_archetype is present (not empty, not "None"): Use that archetype's hook framing from the ICP Archetype section above, grounded in the specific detail from archetype_evidence, written in German — not a generic restatement of the archetype label itself.
If no news and no archetype: Reference one signal as an observation about what it implies, not what it is. If esp_detected is present and esp_score >= 75, reference the ESP tool by name and what running loyalty, franchise communications, and transactional sends through it at their scale likely feels like. Approximate language only — never exact numbers. Open with the implication, not the fact.

P2 — Agitate:
Why this problem is harder than it looks for a company at their scale. 1-2 sentences. No Brevo. No metrics.
If icp_archetype is present: Deepen the specific pain from the ICP Archetype section above using archetype_evidence, in German — make the gap concrete, not the generic archetype description.
If no archetype and esp_detected is present and esp_score >= 75: Reference the ESP by name and the specific friction it creates when trying to coordinate loyalty, delivery, and franchise or multi-location communications through a single transactional tool.
If no archetype and esp_detected present but esp_score < 75: Reference the category of pain generically without naming the tool.
If no archetype and no ESP: Use account_narrative to surface friction common to companies like theirs at this stage.

Personalised LP teaser — output this in the email_1_lp_teaser field, but note it is overridden server-side regardless of what you write here, so any natural German sentence is fine.

P3 — Solve:
2 sentences exactly. Sentence 1: "Brevo ist auf [specific angle] spezialisiert." Shape the angle: if icp_archetype is present, use that archetype's positioning from the ICP Archetype section above, in German. Otherwise fall back to signals: has_loyalty_program = die Koordination von Treueprogrammen und Kundenkommunikation über mehrere Kanäle; needs_cdp = die Zusammenführung von Kundendaten in einer einzigen, nutzbaren Ansicht; has_wallet = die Verbindung von Wallet, Loyalty und Marketing-Kanälen; all false = E-Mail und CRM an einem Ort. Sentence 2: interest-based CTA written as a single natural German sentence, and it must name "ein Gespräch" or "einen Anruf" as what the prospect is getting — this link leads to a booking page, so the sentence should make that unambiguous without turning into a direct ask ("lohnt sich ein kurzes Gespräch" is right, "reservieren Sie 15 Minuten" is wrong). This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Lohnt sich ein kurzes Gespräch darüber, wie das zu Ihrem Rollout passt?"

## LinkedIn 1 — Day 3
2-3 sentences. Warm, human. No Brevo. No meeting ask. Specific to their vertical or role. Use "Ich arbeite mit" not "arbeite mit". End with an open question.

## Email 2 — BAB — Day 7
Use your selected Email 2 case study.
Subject: Different signal from Email 1. No dashes.

STRUCTURE: This email has three completely separate parts. Write each one independently. Never blend them.

email_2_hook — ONE sentence only. Hard limit: roughly 10 words maximum. The scroll-stopper. Names the core tension with no setup, no context, no explanation. If icp_archetype is present, you may draw on that archetype's hook framing from the ICP Archetype section for inspiration — but write your own sharp German sentence, never a verbatim copy of the reference phrase.

email_2_paragraph_1 — 1-2 sentences. The before state. Expand on the tension from the hook — why it is real and specific for a company like theirs at their scale. If icp_archetype is present, ground this in archetype_evidence for a specific before-state rather than a generic one. Otherwise draw from account_narrative and the selected resource pain_points. Do NOT repeat or paraphrase the hook sentence. No Brevo. No metrics.

email_2_paragraph_2 — 2 sentences exactly, no more. Sentence 1: name the resource company, what they changed, and the key metric as a narrative "X ist passiert, was bedeutete Y" — never as a standalone statistic or percentage. Brevo can appear naturally in this sentence as part of the story. Sentence 2: offer-based CTA written as a single natural German sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence.

## Email 3 — Scenario + Resource — Day 12
Use your selected Email 3 report or ebook.
Subject: Different from Emails 1 and 2.

P1 — Scenario story (2-3 sentences MAX):
Drop the reader straight into a scene without any setup or preamble. Do NOT say "stell dir vor" as a lead-in framing device — the abruptness is intentional. Open with a customer situation the prospect will recognise instantly from their own business. Specific to their vertical and sub-vertical. No feature names. No Brevo. No metrics. Pick the vertical-based scenario below first — if icp_archetype is present, let its pain subtly colour which detail of that same scenario you emphasise, without changing the scenario itself.

Scenario library (select closest match, adapt specifically to their business and vertical, write in German):
- Retail/Convenience: A customer picks up milk and a meal deal every Tuesday. No loyalty mechanic, no reason to choose you over the corner shop next time. A small points nudge tied to visit frequency turns a habit into a preference.
- Retail/Fashion: A customer buys a coat in October and disappears until the next sale. A challenge tied to something they already do keeps the relationship alive without a discount.
- Retail/Footwear: Customer buys boots in October. By January they have forgotten the company exists. A challenge tied to usage turns a seasonal buyer into someone who checks in monthly.
- Food/QSR: Someone orders because they have a voucher. No voucher, no return. A streak mechanic changes the relationship from transactional to habitual.
- Food/Coffee: A regular gets their stamp card stamped but never redeems. A digital status tier gives them something to progress toward beyond a free drink.
- Hospitality/Travel: Guest books once for a conference, never returns. A post-stay challenge tied to their preferences gives them a reason the next search starts with your name.
- Beauty/Wellness: Customer buys moisturiser, uses it 30 days, disappears. A replenishment nudge tied to a points streak keeps the routine alive and the reorder predictable.
- Fintech/Telco: User signs up, completes onboarding, never engages again. A progressive challenge tied to behaviour they already do converts an idle account into an active one.
- Default: A customer makes one purchase and goes quiet. Not because they disliked it, but because there was no reason to return.

P2 — Resource bridge: 1-2 sentences. Connect the scenario to the selected resource as useful context, not as "here is a piece of content". Reference the resource title naturally within the sentence. No Brevo. CTA written as a single natural German sentence. This sentence IS the anchor text. No variable. No placeholder. Just the sentence.

## LinkedIn 2 — Day 13
2-3 sentences. Roughly 40-60 words. Lead with the strongest metric from the Email 2 resource as a narrative sentence "X ist bei Y passiert, was Z bedeutete". Connect to company_name or vertical in one sentence. Warm open question. No Brevo.

## Email 4 — Breakup — Day 18
Subject: 2 words max, no punctuation.
P1: 1-2 sentences. Acknowledge no reply without guilt or pressure. Binary choice: not a priority so I will stop, or worth a short conversation.
P2: 2 sentences. Sentence 1: metric from Email 2 reframed as opportunity cost, narrative form, "Unternehmen, die X machen, sehen Y". If icp_archetype is present, keep this consistent with the same archetype pain used earlier in the sequence rather than introducing a new angle — this is the closing note of one continuous thread, not a fresh pitch. Sentence 2: soft door-open CTA written as a single natural German sentence. This sentence IS the anchor text. No variable. No placeholder. Leave the door open without pressure.

## Output — return ONLY this JSON, nothing else:
{
  "selected_resource_email2_id": "",
  "selected_resource_email2_title": "",
  "selected_resource_email3_id": "",
  "selected_resource_email3_title": "",
  "subject_line_1": "",
  "email_1_paragraph_1": "",
  "email_1_paragraph_2": "",
  "email_1_lp_teaser": "",
  "email_1_paragraph_3": "",
  "linkedin_message_1": "",
  "subject_line_2": "",
  "email_2_hook": "",
  "email_2_paragraph_1": "",
  "email_2_paragraph_2": "",
  "subject_line_3": "",
  "email_3_paragraph_1": "",
  "email_3_paragraph_2": "",
  "linkedin_message_2": "",
  "subject_line_4": "",
  "email_4_paragraph_1": "",
  "email_4_paragraph_2": ""
}
"""


# Structural rules identical to the English/German prompts — only the
# Voice/Global Rules section changes. No Brevo French Tone-of-Voice deck was
# available to adapt from (unlike DE), so this uses standard professional
# French B2B conventions instead: vouvoiement throughout (never tutoiement —
# the safe, universal register for a cold email to a contact you don't know,
# regardless of seniority), and a banned-jargon list translated/adapted from
# the English one rather than copied from a brand deck. Flag for review if
# Brevo has (or produces) a French ToV reference, the same way the German
# section was built from one.
_PROMPT_TEMPLATE_FR = """You are a B2B outbound copywriter for Brevo, writing for the French market. Generate a personalised outbound sequence AND select the two best resources from the library below. Write ALL prose output fields in French. Keep the JSON keys exactly as shown (in English) — only the values are French. Return ONLY a single JSON object. No preamble, no markdown.

## Contact & Company Data
- first_name: $first_name
- last_name: $last_name
- job_title: $job_title
- market: $market
- company_name: $company_name
- vertical: $vertical
- esp_detected: $esp_detected
- esp_score: $esp_score
- account_fit_score: $account_fit_score
- relevance_score: $relevance_score
- has_loyalty_program: $has_loyalty_program
- needs_cdp: $needs_cdp
- has_wallet: $has_wallet
- account_narrative: $account_narrative
- email_crm_activity: $email_crm_activity
- icp_archetype: $icp_archetype
- archetype_evidence: $archetype_evidence

## Live News
$news_instruction

## Resource Shortlist
The resources below have already been pre-filtered for this contact by language, vertical, signals, and ICP archetype fit — most are already French-language content, but if any came through in English, extract the facts and metrics faithfully and write your own sentences fully in French rather than copying English phrases into the output.
$resources_json

## Resource Selection Rules
Select TWO resources from the shortlist above. They must always be different assets.

EMAIL 2 RESOURCE — must have "type": "case_study". Pick the one whose best_for_verticals, best_for_signals, or archetype_fit line up best with this contact. If icp_archetype is present, prefer a resource whose archetype_fit list includes it.

EMAIL 3 RESOURCE — must NOT be "type": "case_study" (i.e. an ebook or similar). Must differ from the Email 2 resource. Pick the closest match the same way.

If the shortlist has no case_study, or no non-case_study, pick the closest available resource rather than leaving a field blank.

## ICP Archetype — Messaging Angle (drives Email 1-4)
If icp_archetype is not empty and not "None", it is the single strongest signal available for this contact — sharper and more specific than the generic ESP-based fallback used elsewhere. Use archetype_evidence (never your own guess) as the concrete detail behind the hook, agitation, and positioning throughout the sequence, written in French. If icp_archetype is empty or "None", ignore this section entirely and fall back to the ESP/account_narrative waterfall described in each email's own instructions below.

Per-archetype angle (write your French copy from these English descriptions — do not copy them verbatim):
- Graduate: hook framing = what got them this far will not scale much further. Pain = growing fast enough that a basic ESP is starting to show its limits. Positioning (Email 1 P3) = helping fast-growing teams move beyond a basic ESP without jumping straight to enterprise complexity.
- Network: hook framing = keeping every location saying the same thing at the same time. Pain = central control over messaging breaking down as locations multiply. Positioning = keeping every location's communications consistent from one place.
- Consolidator: hook framing = another tool, another login, another version of the truth. Pain = tool sprawl and fragmented customer data someone is already trying to rationalise. Positioning = bringing loyalty, CRM, and messaging into one platform instead of several.
- Email Specialist: hook framing = email carrying the whole relationship with no room for anything more. Pain = high transactional volume running through a tool that was never built for marketing too. Positioning = combining transactional and marketing email in one platform built for real volume.
- Feature Specialist: hook framing = the new programme launched, but the system underneath has not caught up. Pain = a loyalty, wallet, or WhatsApp launch running ahead of what the current CRM can actually support. Positioning = connecting the new capability directly to the CRM that runs the rest of the business.
- Saver: hook framing = paying enterprise prices for what is actually getting used. Pain = cost pressure on an expensive incumbent tool, often around a renewal. Positioning = the same core capability without the enterprise price tag.

## Voice — Ton et style en français (most important rule)
Toujours vouvoyer ("vous/votre"), jamais tutoyer. C'est la norme pour un premier email envoyé à quelqu'un que vous ne connaissez pas encore, quel que soit son niveau hiérarchique. Non négociable.

Écrivez comme si vous parliez à un collègue que vous respectez, pas comme si vous présentiez un argumentaire commercial. Phrases courtes, mots simples. Si une phrase ne sonnerait pas naturelle dite à voix haute autour d'un café, reformulez-la plus simplement.

Le destinataire est occupé. Vous avez cinq secondes. Tout ce qui ressemble à un post LinkedIn, une plaquette commerciale, ou un rapport de conseil sera supprimé avant la fin de la première ligne.

N'utilisez JAMAIS ces mots ou expressions — ce sont les signes d'un email commercial générique :
- points de contact
- pile technologique / stack (quand vous voulez dire outils ou logiciels)
- infrastructure (au sens générique)
- synchronisé / synchronisation / en phase (décrivez plutôt quoi précisément)
- parcours client
- expérience client
- cycle de vie (sous toutes ses formes : "emails de cycle de vie", "communications de cycle de vie")
- segmentation / segmenter (dites "répartir les clients en groupes" ou décrivez précisément)
- déclenché par le comportement (dites "envoyer un message en fonction de ce que quelqu'un vient de faire")
- orchestration / orchestrer
- activation / activer (au sens marketing)
- multicanal / omnicanal
- friction / signal (quand vous voulez dire une preuve ou un indice)
- vit en silo / vit de manière isolée (décrivez juste quoi)
- tirer parti de / de manière fluide / ravi(e) / enthousiaste / révolutionner / un vrai changement de paradigme
- la marque (au sens générique)
- « C'est là qu'intervient X »
- « Je voulais vous contacter »
- « J'espère que vous allez bien »
- « Je sais que vous êtes occupé(e) »
Aucun point d'exclamation. Jamais.

Table de substitution — quand vous voulez dire :
- « points de contact » → « les endroits où vos clients vous voient » / « les endroits où vos clients ont de vos nouvelles »
- « infrastructure » → « votre système » / « vos outils »
- « stack » → « vos outils » / nommez l'outil directement
- « parcours client » → « ce que vit un client » / « comment un client passe de X à Y »
- « communications de cycle de vie » → « les emails que vous envoyez au fil du temps » / décrivez le déclencheur (« l'email qu'un client reçoit après avoir réservé »)
- « segmentation » → « répartir les clients en groupes » ou décrivez précisément (« envoyer une chose aux clients fidèles, une autre aux nouveaux »)
- « déclenché par le comportement » → « envoyer en fonction de ce que quelqu'un vient de faire »
- « vit en silo » → « vit dans des endroits séparés »

Test de voix avant de rendre le texte : lisez chaque phrase à voix haute. Si elle sonne comme une présentation sur scène, reformulez-la. Si elle sonne comme si vous expliquiez quelque chose à un collègue, gardez-la.

Écrivez avec du relief. Un vrai email a parfois une pensée incomplète. Une phrase qui commence par « Et » ou « Mais ». Une observation qui ne bascule pas immédiatement vers une solution.

## Global Rules
- Zero em dashes or en dashes. Utilisez une virgule ou deux phrases à la place.
- Phrases courtes et claires, niveau de lecture simple. Si une phrase dépasse environ 18 mots, coupez-la. Préférez toujours le mot le plus court quand une option existe.
- N'utilisez jamais d'abréviations — écrivez les mots en entier.
- Ne traduisez jamais le terme "AI" — gardez "AI" tel quel dans le texte français, jamais "IA".
- Insérez une espace avant le signe pourcentage, par exemple "20 %" et non "20%".
- Devise : symbole après le nombre, virgule comme séparateur décimal, espace comme séparateur de milliers, par exemple "9,99 €" et "1 000 €". Omettez ",00" quand il n'y a pas de centimes : "10 €" et non "10,00 €".
- Plus de "vous/votre" que de "je/nous/notre" dans chaque email. EXCEPTION : Email 1 paragraphe 1 quand une actualité récente est disponible — "Je suis tombé(e) sur..." ou "J'ai remarqué..." est permis et encouragé pour signaler une vraie recherche.
- 1-2 phrases par paragraphe. Écrivez pour un écran de mobile.
- Emails 1-3 : 75-125 mots au total. Email 4 : 50-80 mots. Comptez avant de rendre le texte.
- Les CTA sont toujours basés sur l'intérêt ou une offre. Ne demandez JAMAIS directement un rendez-vous (pas de "réservez 15 minutes", pas de "planifions un appel"). Exception : le CTA de clôture de l'Email 1 (P3) mène vers une page de réservation, donc sa phrase doit quand même nommer "un appel" ou "un échange" comme destination — ton doux, mais clair sur ce que le clic déclenche, pour que le prospect ne soit jamais surpris. Le CTA est toujours la dernière phrase de l'email.
- La dernière phrase EST le texte d'ancrage. Lemlist la transforme en lien cliquable. N'incluez jamais {cta_book_call}, {case_study_url}, {report_url}, ni aucune variable dans le texte. Écrivez uniquement la phrase. Pas de placeholder. Pas de crochets.
- Aucune métrique dans l'Email 1 ou l'Email 3. Les métriques apparaissent d'abord dans l'Email 2.
- Brevo apparaît une fois dans l'Email 1 (phrase de transition uniquement, avec "Brevo est spécialisé dans"), naturellement dans l'Email 2, jamais dans l'Email 3 ou 4.

## Email 1 — PAS — Jour 1
Subject line rules — s'appliquent aux quatre emails :
- 2-6 mots, tout en minuscules, aucune ponctuation sauf "?"
- Pas de prénom, pas de verbe comme premier mot
- Doit suggérer la douleur que cet email adresse sans l'expliquer
- Le destinataire doit ressentir un petit manque que seule l'ouverture de l'email comble
- Doit sonner comme un email interne transféré entre collègues, pas comme un objet marketing
- Ne jamais décrire une chose ou nommer un concept — créer une tension ou suggérer un manque

Test de qualité avant de rendre le texte : cet objet aurait-il pu être envoyé tel quel à 1 000 autres entreprises ? Si oui, réécrivez-le jusqu'à ce qu'il soit spécifique à leur univers.

Subject line formula by email:
EMAIL 1 objet : suggérez la douleur liée aux communications ou à la fidélité client. Ne nommez jamais directement l'ESP. Ne faites jamais référence à l'actualité dans l'objet, elle appartient au corps de l'email. Adaptez au secteur et aux signaux.
EMAIL 2 objet : créez une comparaison ou un contraste qui suggère qu'une meilleure solution existe. Style : "X vs Y" ou "X sans Y". Adaptez au secteur et aux signaux.
EMAIL 3 objet : nommez ce qui ne fonctionne plus ou ce qui manque, jamais la solution. Adaptez au secteur et aux signaux.
EMAIL 4 objet : toujours l'équivalent de "dernier message" / "une dernière chose" (2 mots maximum). Aucune variation.

P1 — Accroche actualité ou signal :
RÈGLE CRITIQUE : ne répétez jamais des faits que le prospect connaît déjà sur sa propre entreprise. Votre rôle n'est pas de l'informer, c'est de relier quelque chose que vous avez observé à une tension qu'il ressent mais n'a pas encore résolue.
Si une actualité récente a été trouvée : commencez par "Je suis tombé(e) sur..." ou "J'ai remarqué..." — c'est le seul endroit de toute la séquence où commencer par "Je" n'est pas seulement permis, mais requis. Présentez ce que vous avez trouvé comme quelque chose qui vous a fait penser à un défi opérationnel précis, pas comme une reformulation de faits qu'ils connaissent déjà. 1-2 phrases. Pas de Brevo. Pas de métrique.
Si pas d'actualité mais icp_archetype présent (ni vide ni "None") : utilisez l'angle d'accroche de cet archétype depuis la section ICP Archetype ci-dessus, ancré dans le détail précis d'archetype_evidence, écrit en français — pas une reformulation générique du libellé de l'archétype lui-même.
Si ni actualité ni archétype : mentionnez un signal comme une observation sur ce qu'il implique, pas ce qu'il est. Si esp_detected est présent et esp_score >= 75, nommez l'outil ESP et ce que gérer la fidélité, les communications multi-sites et les envois transactionnels via cet outil à leur échelle donne probablement comme sensation. Langage approximatif uniquement, jamais de chiffres exacts.

P2 — Agiter :
Pourquoi ce problème est plus difficile qu'il n'y paraît pour une entreprise de leur taille. 1-2 phrases. Pas de Brevo. Pas de métrique.
Si icp_archetype présent : approfondissez la douleur spécifique de la section ICP Archetype ci-dessus en utilisant archetype_evidence, en français — rendez le manque concret et spécifique à ce que vous avez trouvé, pas la description générique de l'archétype.
Si pas d'archétype et esp_detected présent avec esp_score >= 75 : nommez l'ESP et la friction spécifique qu'il crée pour coordonner fidélité, livraison et communications multi-sites via un seul outil transactionnel.
Si pas d'archétype et ESP présent mais esp_score < 75 : mentionnez la catégorie de douleur de façon générique, sans nommer l'outil.
Si pas d'archétype et pas d'ESP : utilisez account_narrative pour faire émerger une friction courante chez des entreprises à ce stade.

Personalised LP teaser — sits between P2 and P3 as a standalone line. Output this in the email_1_lp_teaser field, but note it is overridden server-side regardless of what you write here, so any natural French sentence is fine.

P3 — Résoudre :
2 phrases exactement. Phrase 1 : "Brevo est spécialisé dans [angle spécifique]." Façonnez l'angle : si icp_archetype présent, utilisez le positionnement de cet archétype depuis la section ICP Archetype ci-dessus, en français. Sinon, appuyez-vous sur les signaux : has_loyalty_program = coordonner la fidélité et les communications clients sur tous les canaux ; needs_cdp = unifier les données clients en une seule vue exploitable ; has_wallet = relier wallet, fidélité et canaux marketing ; tout à false = email et CRM au même endroit. Phrase 2 : CTA basé sur l'intérêt, écrit comme une phrase naturelle unique, qui doit nommer "un appel" ou "un échange" comme ce que le prospect obtient — ce lien mène vers une page de réservation, la phrase doit donc le rendre clair sans devenir une demande directe ("cela vaut-il un rapide échange" convient, "réservez 15 minutes" ou "planifions un appel" ne convient pas). Cette phrase EST le texte d'ancrage, Lemlist la transforme en lien. Pas de variable. Pas de placeholder. Juste la phrase. Exemple : "Cela vaut-il un rapide échange sur la façon dont cela s'appliquerait à votre déploiement ?"

## LinkedIn 1 — Jour 3
2-3 phrases. Chaleureux, humain. Pas de Brevo. Pas de demande de rendez-vous. Spécifique à leur secteur ou rôle. Utilisez "je travaille avec" plutôt que "travaillant avec". Terminez par une question ouverte.

## Email 2 — BAB — Jour 7
Use your selected Email 2 case study.
Objet : signal différent de l'Email 1. Pas de tirets.

STRUCTURE : cet email a trois parties totalement séparées. Écrivez chacune indépendamment. Ne les mélangez jamais. Ne laissez jamais une phrase faire le travail de deux parties.

email_2_hook — UNE seule phrase. Limite stricte : 12 mots maximum. C'est l'accroche qui arrête le scroll. Elle nomme la tension centrale sans mise en contexte, sans explication. Elle tient seule comme son propre bloc visuel. Le lecteur doit ressentir le problème immédiatement, sans avoir besoin du paragraphe suivant pour comprendre. Si icp_archetype présent, vous pouvez vous inspirer de l'angle d'accroche de cet archétype depuis la section ICP Archetype, mais écrivez votre propre phrase percutante, jamais une copie mot pour mot de la phrase de référence.

email_2_paragraph_1 — 1-2 phrases. L'état "avant". Développez la tension de l'accroche : pourquoi elle est réelle et spécifique pour une entreprise de leur taille. Si icp_archetype présent, ancrez ceci dans archetype_evidence pour un état "avant" spécifique plutôt que générique. Sinon appuyez-vous sur account_narrative et les pain_points de la ressource sélectionnée. NE répétez PAS et ne paraphrasez PAS la phrase d'accroche. Pas de Brevo. Pas de métrique.

email_2_paragraph_2 — 2 phrases exactement, pas plus. Phrase 1 : nommez l'entreprise de la ressource, ce qu'elle a changé, et la métrique clé sous forme narrative "X s'est passé, ce qui a signifié Y" — jamais comme une statistique ou un pourcentage isolé. Brevo peut apparaître naturellement dans cette phrase, comme partie de l'histoire. Phrase 2 : CTA basé sur une offre, écrit comme une phrase naturelle unique. Cette phrase EST le texte d'ancrage, Lemlist la transforme en lien. Pas de variable. Pas de placeholder. Juste la phrase. Exemple : "Voici comment ils ont fait la bascule"

## Email 3 — Scénario + Ressource — Jour 12
Use your selected Email 3 report or ebook.
Objet : différent des Emails 1 et 2.

P1 — Scénario (2-3 phrases MAX) :
Plongez le lecteur directement dans une scène, sans mise en contexte ni préambule. Ne dites PAS "imaginez" ou "imaginons" comme amorce. N'ajoutez pas de phrase d'introduction avant la scène, l'aspect abrupt est intentionnel et rompt le schéma classique d'un email commercial. Ouvrez sur une situation client que le prospect reconnaîtra instantanément dans son propre secteur. Spécifique à leur secteur et sous-secteur. Référencez leur produit ou service réel quand c'est possible. Montrez un manque qu'un engagement client plus intelligent pourrait combler. Pas de nom de fonctionnalité. Pas de Brevo. Pas de métrique. Choisissez d'abord le scénario ci-dessous correspondant à leur secteur ; si icp_archetype présent, laissez sa douleur colorer subtilement le détail du même scénario que vous mettez en avant, sans changer le scénario lui-même.

Scenario library (choisissez le plus proche, adaptez-le précisément à leur entreprise et secteur) :
- Retail/Convenience : un client prend du lait et un menu déjeuner chaque mardi. Aucun mécanisme de fidélité, aucune raison de vous préférer à l'épicerie du coin la prochaine fois. Un petit coup de pouce en points lié à la fréquence de visite transforme une habitude en préférence.
- Retail/Fashion : un client achète un manteau en octobre et disparaît jusqu'aux prochains soldes. Un défi lié à quelque chose qu'il fait déjà, comme noter son dernier achat pour gagner des points, garde la relation vivante sans remise.
- Retail/Footwear : un client achète des bottes en octobre. En janvier, il a oublié l'existence de l'entreprise. Un défi lié à l'usage, comme parcourir 50 km pour débloquer sa prochaine récompense, transforme un acheteur saisonnier en quelqu'un qui revient chaque mois.
- Food/QSR : quelqu'un commande parce qu'il a un bon de réduction. Sans bon, pas de retour. Un mécanisme de série, comme trois commandes ce mois-ci pour débloquer un accompagnement gratuit, change la relation de transactionnelle à habituelle.
- Food/Coffee : un habitué fait tamponner sa carte de fidélité mais ne l'utilise jamais. Un statut numérique progressif donne une progression à viser au-delà d'une simple boisson gratuite.
- Hospitality/Travel : un client réserve une fois pour une conférence, ne revient jamais. Un défi post-séjour lié à ses préférences lui donne une raison pour que sa prochaine recherche commence par votre nom.
- Beauty/Wellness : un client achète une crème hydratante, l'utilise 30 jours, disparaît. Un rappel de réapprovisionnement lié à une série de points garde la routine vivante et le réachat prévisible.
- Fintech/Telco : un utilisateur s'inscrit, termine l'onboarding, ne revient jamais. Un défi progressif lié à un comportement qu'il a déjà convertit un compte inactif en compte actif.
- Default : un client fait un seul achat puis disparaît. Pas parce qu'il n'a pas aimé, mais parce qu'il n'avait aucune raison de revenir.

P2 — Pont vers la ressource : 1-2 phrases. Reliez le scénario à la ressource sélectionnée comme un contexte utile, pas comme "voici un contenu". Mentionnez le titre de la ressource naturellement dans la phrase. Pas de Brevo. CTA écrit comme une phrase naturelle unique. Cette phrase EST le texte d'ancrage, Lemlist la transforme en lien. Pas de variable. Pas de placeholder. Juste la phrase. Exemple : "Avec plaisir pour vous envoyer le guide complet si utile"

## LinkedIn 2 — Jour 13
2-3 phrases. Environ 40-60 mots. Ouvrez avec la métrique la plus forte de la ressource de l'Email 2 sous forme narrative "X s'est passé pour Y, ce qui a signifié Z". Reliez à company_name ou au secteur en une phrase. Question ouverte chaleureuse. Pas de Brevo.

## Email 4 — Rupture — Jour 18
Objet : 2 mots maximum, aucune ponctuation. Choisissez : "toujours ouvert" / "dernier message" / "une dernière chose"
P1 : 1-2 phrases. Reconnaissez l'absence de réponse sans culpabiliser ni mettre de pression. Choix binaire : pas une priorité donc j'arrête, ou cela vaut un court échange.
P2 : 2 phrases. Phrase 1 : métrique de l'Email 2 reformulée comme coût d'opportunité, sous forme narrative, "les entreprises qui font X voient Y". Si icp_archetype présent, restez cohérent avec la même douleur d'archétype utilisée plus tôt dans la séquence plutôt que d'introduire un nouvel angle — c'est la note de clôture d'un seul fil continu, pas un nouveau pitch. Phrase 2 : CTA doux qui laisse la porte ouverte, écrit comme une phrase naturelle unique. Cette phrase EST le texte d'ancrage, Lemlist la transforme en lien. Pas de variable. Pas de placeholder. Laissez la porte ouverte sans pression. Exemple : "Si le moment est venu, voici un lien vers mon agenda"

## Output — return ONLY this JSON, nothing else:
{
  "selected_resource_email2_id": "",
  "selected_resource_email2_title": "",
  "selected_resource_email3_id": "",
  "selected_resource_email3_title": "",
  "subject_line_1": "",
  "email_1_paragraph_1": "",
  "email_1_paragraph_2": "",
  "email_1_lp_teaser": "",
  "email_1_paragraph_3": "",
  "linkedin_message_1": "",
  "subject_line_2": "",
  "email_2_hook": "",
  "email_2_paragraph_1": "",
  "email_2_paragraph_2": "",
  "subject_line_3": "",
  "email_3_paragraph_1": "",
  "email_3_paragraph_2": "",
  "linkedin_message_2": "",
  "subject_line_4": "",
  "email_4_paragraph_1": "",
  "email_4_paragraph_2": ""
}
"""


def _build_content_prompt(contact: dict, company: dict, news_instruction: str, resources_json: str) -> str:
    """Substitute contact + company + news + resources into the master template.
    Contacts in DE/AT/CH get the German-voice prompt variant, FR contacts get
    the French-voice variant, everyone else gets the English default — same
    structure, JSON schema, and CTA-anchor mechanics throughout, but written
    natively in each language rather than generated in English and translated
    afterward."""
    from string import Template
    market = (contact.get("market") or company.get("market") or "").strip()
    if market in _DACH_MARKETS:
        template = _PROMPT_TEMPLATE_DE
    elif market in _FR_MARKETS:
        template = _PROMPT_TEMPLATE_FR
    else:
        template = _PROMPT_TEMPLATE
    return Template(template).safe_substitute(
        first_name           = contact.get("first_name") or "",
        last_name            = contact.get("last_name") or "",
        job_title            = contact.get("job_title") or "",
        market               = contact.get("market") or company.get("market") or "",
        company_name         = company.get("company_name") or contact.get("company_name") or "",
        vertical             = company.get("vertical") or "",
        esp_detected         = company.get("esp_detected") or "unknown",
        esp_score            = company.get("esp_score") if company.get("esp_score") is not None else 0,
        account_fit_score    = company.get("account_fit_score") if company.get("account_fit_score") is not None else 0,
        relevance_score      = contact.get("relevance_score") if contact.get("relevance_score") is not None else 0,
        has_loyalty_program  = bool(company.get("has_loyalty_program")),
        needs_cdp            = bool(company.get("needs_cdp")),
        has_wallet           = bool(company.get("has_wallet")),
        account_narrative    = company.get("account_narrative") or "",
        email_crm_activity   = company.get("email_crm_activity") or "",
        # "None" (literal string) means the archetype search ran and found no
        # match — a valid, complete result, distinct from true NULL (never
        # classified). Passed through as-is: the prompt's own instructions
        # explicitly treat the "None" string the same as empty, so no
        # extra normalisation is needed here.
        icp_archetype        = company.get("icp_archetype_primary") or "",
        archetype_evidence   = company.get("icp_archetype_evidence") or "",
        news_instruction     = news_instruction,
        resources_json       = resources_json,
    )


def _build_batch_requests(
    contacts: list[dict],
    company_map: dict,
    news_map: dict,
) -> list[dict]:
    requests = []
    for c in contacts:
        company = company_map.get((c["domain"], c.get("market") or ""), {})
        domain = (c.get("domain") or "").strip().lower()
        news = news_map.get(domain, {"found": False, "usable": False})
        market = c.get("market") or company.get("market") or ""
        archetype = company.get("icp_archetype_primary") or ""
        shortlist = shortlist_resources(company, market=market, icp_archetype=archetype)
        resources_json = json.dumps(shortlist, indent=2, ensure_ascii=False)
        prompt = _build_content_prompt(c, company, _news_instruction(news), resources_json)
        requests.append({
            "custom_id": _encode_custom_id(c["id"]),
            "params": {
                "model":      "claude-sonnet-4-6",
                "max_tokens": 4000,
                "system":     _SYSTEM,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
        })
    return requests


# ── CTA post-processing ───────────────────────────────────────────────────────

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+", re.DOTALL)


def _split_cta(text: str) -> tuple[str, str]:
    """Split a multi-sentence paragraph into (body_minus_last, last_sentence).

    The last sentence is the anchor text Lemlist wraps as a link. If the
    paragraph is a single sentence, body is empty and the whole sentence
    becomes the CTA.

    Handles the case where the final "sentence" has no terminal punctuation
    (the model occasionally writes "Here is how they made it work" with no
    period); we recover the trailing fragment so it becomes the CTA rather
    than being silently swallowed into the body.
    """
    text = (text or "").strip()
    if not text:
        return ("", "")
    parts = _SENTENCE_RE.findall(text)
    consumed_len = sum(len(p) for p in parts)
    trailing = text[consumed_len:].strip()
    if trailing:
        parts.append(trailing)
    if len(parts) < 2:
        return ("", text)
    return ("".join(parts[:-1]).strip(), parts[-1].strip())


def _post_process(content_json: dict, personalised_lp_url: str = "", market: str = "") -> dict:
    """Override the LP teaser (canonical anchor text), inject resource URLs
    looked up by selected id, stamp the personalised LP URL minted by
    lp_generator, and split the four CTA paragraphs into body + cta columns
    for Lemlist consumption.

    Resource URLs are looked up server-side rather than asked of the model
    so we never serve a hallucinated link. If the model picks an unknown
    resource id, the url field is empty and we log a warning. The
    personalised LP URL comes from company_lp_cache (per-domain, minted
    once) and is empty if minting failed for that domain — Lemlist would
    then need to skip the teaser link for that contact.

    `market` selects the LP teaser language — DE/AT/CH contacts get the
    German anchor text and FR contacts get the French one (matching the
    prompt variant they were generated with), everyone else gets English.
    """
    out = dict(content_json)
    market_norm = (market or "").strip()
    if market_norm in _DACH_MARKETS:
        out["email_1_lp_teaser"] = _LP_TEASER_DE
    elif market_norm in _FR_MARKETS:
        out["email_1_lp_teaser"] = _LP_TEASER_FR
    else:
        out["email_1_lp_teaser"] = _LP_TEASER
    out["personalised_lp_url"] = personalised_lp_url or ""

    resources_by_id = {r["id"]: r for r in get_all_resources()}
    for slot in ("email2", "email3"):
        rid = (out.get(f"selected_resource_{slot}_id") or "").strip()
        resource = resources_by_id.get(rid)
        if resource:
            out[f"selected_resource_{slot}_url"] = resource.get("url") or ""
        else:
            out[f"selected_resource_{slot}_url"] = ""
            if rid:
                logger.warning(
                    "content: model picked unknown resource id %r for %s — url left empty",
                    rid, slot,
                )

    for src, body_key, cta_key in _CTA_SPLITS:
        body, cta = _split_cta(out.get(src) or "")
        out[body_key] = body
        out[cta_key] = cta
    return out


# ── Submit ────────────────────────────────────────────────────────────────────

async def submit_content(limit: int | None = None, markets: set[str] | list[str] | None = None) -> dict:
    """
    Reads sourced_contacts with no content_generated_at, enriches with company
    context from priority_tam, fetches per-domain news, submits to Claude
    Batch API in chunks of 500, and records jobs in contact_content_batches.

    `markets` restricts this call to a subset (e.g. {"US", "FR"}) for a
    one-off run covering only those markets — defaults to
    CONTENT_GENERATION_MARKETS (the daily cron's standing behavior), same
    pattern as monthly_batch.py's run_monthly_batch(groups=...).
    """
    sb = get_supabase()
    allowed_markets = list(markets) if markets is not None else list(CONTENT_GENERATION_MARKETS)

    if limit:
        contacts = (
            sb.table("sourced_contacts")
            .select("id, domain, email, first_name, last_name, job_title, seniority, company_name, market, relevance_score")
            .is_("content_generated_at", "null")
            .in_("market", allowed_markets)
            .limit(limit)
            .execute()
            .data
        )
    else:
        contacts = fetch_all(
            "sourced_contacts",
            "id, domain, email, first_name, last_name, job_title, seniority, company_name, market, relevance_score",
            [("is_", "content_generated_at", "null"), ("in_", "market", allowed_markets)],
        )

    if not contacts:
        logger.info("content: no contacts pending generation")
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

    # Enrich with priority_tam company context
    domains = list({c["domain"] for c in contacts})
    company_rows = fetch_all(
        "priority_tam",
        "domain, market, company_name, vertical, account_narrative, account_fit_score, "
        "employee_range, email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "esp_detected, esp_score, icp_archetype_primary, icp_archetype_secondary, icp_archetype_evidence",
        [("in_", "domain", domains)],
    )
    company_map = {(r["domain"], r.get("market", "")): r for r in company_rows}

    # Per-domain news + LP minting (both cached forever per domain) —
    # only pay once per company across all batches.
    unique_news: list[tuple[str, str]] = []
    unique_lp: list[dict] = []
    seen_domains: set[str] = set()
    for c in contacts:
        d = (c.get("domain") or "").strip().lower()
        if not d or d in seen_domains:
            continue
        seen_domains.add(d)
        company = company_map.get((c["domain"], c.get("market") or ""), {})
        name = company.get("company_name") or c.get("company_name") or ""
        unique_news.append((d, name))
        unique_lp.append({
            "domain":                d,
            "company_name":          name,
            "industry":              company.get("vertical"),
            "market":                c.get("market") or company.get("market"),
            "esp_detected":          company.get("esp_detected"),
            "esp_score":             company.get("esp_score"),
            "icp_archetype_primary":   company.get("icp_archetype_primary"),
            "icp_archetype_secondary": company.get("icp_archetype_secondary"),
            "icp_archetype_evidence":  company.get("icp_archetype_evidence"),
            "account_fit_reasoning": company.get("account_narrative"),
            "account_fit_score":     company.get("account_fit_score"),
            "has_loyalty_program":   company.get("has_loyalty_program"),
            "has_wallet":            company.get("has_wallet"),
            "needs_cdp":             company.get("needs_cdp"),
            "email_crm_activity":    company.get("email_crm_activity"),
        })

    logger.info(
        "content: pre-fetching news + landing pages for %d unique domains",
        len(unique_news),
    )
    news_map, lp_map = await asyncio.gather(
        fetch_news_many(unique_news),
        fetch_lp_many(unique_lp),
    )
    usable_count = sum(1 for n in news_map.values() if n.get("found") and n.get("usable"))
    logger.info(
        "content: ready — %d/%d news usable, %d/%d LPs minted",
        usable_count, len(news_map), len(lp_map), len(unique_lp),
    )

    client = _get_client()
    chunks = [contacts[i : i + _BATCH_SIZE] for i in range(0, len(contacts), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(
            requests=_build_batch_requests(chunk, company_map, news_map)
        )
        mapping = {
            _encode_custom_id(c["id"]): {
                "contact_id": c["id"],
                "email":      c.get("email"),
                "domain":     c["domain"],
                "market":     c.get("market") or "",
            }
            for c in chunk
        }
        sb.table("contact_content_batches").insert({
            "batch_id":           batch.id,
            "model":              "claude-sonnet-4-6",
            "status":             "pending",
            "contacts_submitted": len(chunk),
            "request_mapping":    mapping,
        }).execute()
        logger.info("content: submitted batch %s for %d contacts", batch.id, len(chunk))
        return batch.id

    batch_ids = await asyncio.gather(*[submit_chunk(c) for c in chunks])
    logger.info("content: %d batches submitted, %d contacts total", len(batch_ids), len(contacts))
    return {"status": "ok", "submitted": len(contacts), "batches": len(batch_ids), "batch_ids": list(batch_ids)}


# ── Sample generation (sync, non-batch) ──────────────────────────────────────

async def generate_one(contact: dict, company: dict, news: dict, lp_url: str = "") -> dict:
    """One-off synchronous generation for sample/preview workflows. Calls
    Claude Messages directly (not Batch) so results come back in seconds.
    Returns the post-processed JSON (LP teaser overridden, personalised LP
    URL stamped, resource URLs injected, CTAs split)."""
    market = contact.get("market") or company.get("market") or ""
    archetype = company.get("icp_archetype_primary") or ""
    shortlist = shortlist_resources(company, market=market, icp_archetype=archetype)
    resources_json = json.dumps(shortlist, indent=2, ensure_ascii=False)
    prompt = _build_content_prompt(contact, company, _news_instruction(news), resources_json)
    client = _get_client()
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = (message.content[0].text or "").strip()
    if "```" in raw_text:
        raw_text = raw_text.split("```", 1)[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.rsplit("```", 1)[0].strip()
    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    if start != -1 and end > start:
        raw_text = raw_text[start:end]
    market = contact.get("market") or company.get("market") or ""
    return _post_process(json.loads(raw_text), personalised_lp_url=lp_url, market=market)


@router.post("/pipelines/content/preview")
async def content_preview(request: Request, x_preview_secret: str | None = Header(None)):
    """One-off synchronous generation for manual QA — accepts {contact, company}
    in the request body (same shapes as generate_one()'s args) and returns the
    real generated sequence directly, plus the real news lookup result under
    "_news_used". Not used by the batch pipeline; exists so real sample output
    can be reviewed without waiting on a Batch API job.

    News is looked up here via fetch_company_news() (the same cache-first
    lookup submit_content() uses), keyed on company["domain"] — it is never
    accepted as user input, since in production this is always something the
    pipeline finds, not something a human supplies.

    Protected by a shared secret (X-Preview-Secret header) since this triggers
    a real, billed Claude API call and would otherwise be a public,
    unauthenticated way to spend API credits. Fails closed: if the secret
    isn't configured server-side at all, every request is rejected rather
    than silently allowed through.
    """
    expected = os.environ.get("CONTENT_PREVIEW_SECRET")
    if not expected or not hmac.compare_digest(x_preview_secret or "", expected):
        raise HTTPException(status_code=401, detail="invalid or missing X-Preview-Secret")

    from pipelines.news_search import fetch_company_news

    body = await request.json()
    contact = body.get("contact", {})
    company = body.get("company", {})
    lp_url = body.get("lp_url", "")
    domain = (company.get("domain") or contact.get("domain") or "").strip()
    try:
        news = await fetch_company_news(domain, company.get("company_name") or "") if domain else {"found": False, "usable": False}
        result = await generate_one(contact, company, news, lp_url=lp_url)
        result["_news_used"] = news
        return result
    except Exception as exc:
        logger.exception("content_preview: failed")
        raise HTTPException(status_code=500, detail=str(exc))


_TOOL_HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "content_preview_tool.html")


@router.get("/tools/content-preview")
async def content_preview_tool():
    """Serves the manual QA tool page (form -> live /pipelines/content/preview
    call, same origin so no CORS setup needed). The page itself prompts for
    the X-Preview-Secret and sends it with each generate request."""
    return FileResponse(_TOOL_HTML_PATH, media_type="text/html")


# ── Process results ───────────────────────────────────────────────────────────

async def process_content_results(batch_id: str) -> dict:
    """Polls a batch. If complete, writes outbound_content jsonb to sourced_contacts."""
    client = _get_client()
    batch = await client.messages.batches.retrieve(batch_id)

    if batch.processing_status != "ended":
        return {"status": "pending", "batch_id": batch_id}

    sb = get_supabase()
    batch_row = (
        sb.table("contact_content_batches")
        .select("request_mapping")
        .eq("batch_id", batch_id)
        .execute()
        .data
    )
    request_mapping: dict = batch_row[0]["request_mapping"] if batch_row else {}

    # Bulk-load cached LP URLs for every domain in this batch so each result
    # can be stamped with its personalised_lp_url without one DB round-trip
    # per row. Domains missing from cache get an empty URL.
    domains_in_batch = list({m.get("domain") for m in request_mapping.values() if m.get("domain")})
    lp_rows = (
        sb.table("company_lp_cache")
        .select("domain,preview_url")
        .in_("domain", domains_in_batch)
        .execute()
        .data
        if domains_in_batch else []
    )
    lp_lookup = {r["domain"]: r["preview_url"] for r in lp_rows}

    updates: list[dict] = []
    total_input = 0
    total_output = 0

    async for result in await client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            logger.warning("content: skipping %s result for %s", result.result.type, result.custom_id)
            continue

        meta = request_mapping.get(result.custom_id)
        if not meta:
            logger.warning("content: no mapping found for custom_id %s", result.custom_id)
            continue

        raw_text = result.result.message.content[0].text.strip()
        try:
            if "```" in raw_text:
                raw_text = raw_text.split("```", 1)[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.rsplit("```", 1)[0].strip()
            start = raw_text.find("{")
            end   = raw_text.rfind("}") + 1
            if start != -1 and end > start:
                raw_text = raw_text[start:end]
            content_json = json.loads(raw_text)
        except (json.JSONDecodeError, IndexError) as exc:
            logger.warning("content: failed to parse JSON for %s: %s", result.custom_id, exc)
            continue

        content_json = _post_process(
            content_json,
            personalised_lp_url=lp_lookup.get(meta.get("domain", ""), ""),
            market=meta.get("market", ""),
        )

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        updates.append({
            "id":                   meta["contact_id"],
            "outbound_content":     content_json,
            "content_batch_id":     batch_id,
            "content_generated_at": datetime.now(timezone.utc).isoformat(),
        })

    # Use plain UPDATE per row (not upsert): supabase-py's upsert sends
    # INSERT ... ON CONFLICT DO UPDATE, and Postgres validates NOT NULL
    # constraints on the INSERT path BEFORE the conflict resolution runs,
    # so a partial payload (id + 3 content fields, no domain/email) fails
    # the not-null on `domain` even when the row already exists.
    for upd in updates:
        sb.table("sourced_contacts").update({
            "outbound_content":     upd["outbound_content"],
            "content_batch_id":     upd["content_batch_id"],
            "content_generated_at": upd["content_generated_at"],
        }).eq("id", upd["id"]).execute()

    cost = total_input * _BATCH_INPUT_COST_PER_TOKEN + total_output * _BATCH_OUTPUT_COST_PER_TOKEN
    sb.table("contact_content_batches").update({
        "status":             "completed",
        "contacts_completed": len(updates),
        "input_tokens":       total_input,
        "output_tokens":      total_output,
        "estimated_cost_usd": round(cost, 6),
        "completed_at":       datetime.now(timezone.utc).isoformat(),
    }).eq("batch_id", batch_id).execute()

    logger.info("content: completed batch %s — %d contacts, $%.4f", batch_id, len(updates), cost)
    return {
        "status":             "ok",
        "batch_id":           batch_id,
        "completed":          len(updates),
        "input_tokens":       total_input,
        "output_tokens":      total_output,
        "estimated_cost_usd": round(cost, 4),
    }


# ── Poll all pending ──────────────────────────────────────────────────────────

async def process_all_pending_content() -> dict:
    """Called by enrich-poller every 30 min. Polls pending batches and writes results."""
    sb = get_supabase()
    pending = (
        sb.table("contact_content_batches")
        .select("batch_id")
        .eq("status", "pending")
        .execute()
        .data
    )

    if not pending:
        return {"status": "ok", "pending": 0, "message": "no pending batches"}

    results = await asyncio.gather(*[process_content_results(r["batch_id"]) for r in pending])

    still_pending = sum(1 for r in results if r["status"] == "pending")
    if still_pending:
        logger.info("content: %d/%d batches still pending", still_pending, len(results))
        return {"status": "ok", "pending": still_pending, "completed": len(results) - still_pending}

    total_contacts = sum(r.get("completed", 0) for r in results)
    total_cost     = sum(r.get("estimated_cost_usd", 0) for r in results)

    await notify(
        f"✅ *Contact content generation complete*\n"
        f"• Contacts generated: {total_contacts}\n"
        f"• Batches: {len(results)}\n"
        f"• Estimated cost: ${total_cost:.4f}"
    )

    return {"status": "ok", "pending": 0, "completed": total_contacts, "estimated_cost_usd": round(total_cost, 4)}


# ── Endpoints ─────────────────────────────────────────────────────────────────

async def _submit_content_bg(limit: int | None, markets: set[str] | None) -> None:
    """Runs submit_content() as a background task instead of inline in the
    request handler. The news+LP prefetch phase alone can take several
    minutes for a few hundred unique domains, well past whatever timeout
    Railway's edge proxy enforces on a live HTTP connection — confirmed
    2026-07-28 when two consecutive UKI submissions both returned a generic
    "upstream error" to the client despite (at least once, for a similar
    US+FR run) the work actually completing successfully server-side. A
    background task removes the dependency on the connection surviving at
    all, and reports success/failure to Slack instead of the HTTP response."""
    try:
        result = await submit_content(limit=limit, markets=markets)
        markets_label = ", ".join(sorted(markets)) if markets else "default"
        await notify(
            f"✅ *Content generation submitted* ({markets_label})\n"
            f"• Contacts: {result['submitted']}\n"
            f"• Batches: {result['batches']}"
        )
    except Exception as exc:
        logger.exception("content_submit: background task failed")
        await notify(f"❌ *Content generation submission failed* — `{exc}`", success=False)


@router.post("/pipelines/content/submit")
async def content_submit(background_tasks: BackgroundTasks, limit: int | None = None, markets: str | None = None):
    """Submit sourced_contacts with no content to Claude Batch API. Runs in the
    background (see _submit_content_bg) since the news+LP prefetch phase can
    run long enough to outlast a live HTTP connection. Check Slack for the
    completion notification, or query contact_content_batches directly.
    Pass ?markets=US,FR to restrict to a subset (defaults to CONTENT_GENERATION_MARKETS)."""
    market_set = set(markets.split(",")) if markets else None
    background_tasks.add_task(_submit_content_bg, limit, market_set)
    return {"status": "started"}


async def _content_complete_all_bg() -> None:
    """Same rationale as _submit_content_bg — polling + writing outbound_content
    for thousands of contacts across several batches can run long enough to
    outlast Railway's edge proxy timeout. process_all_pending_content() already
    posts its own Slack notification on full success; this wrapper only adds
    failure reporting, since running inline previously had no way to surface
    an exception once the HTTP connection was gone."""
    try:
        await process_all_pending_content()
    except Exception as exc:
        logger.exception("content_complete_all: background task failed")
        await notify(f"❌ *Content completion poll failed* — `{exc}`", success=False)


@router.post("/pipelines/content-complete-all")
async def content_complete_all(background_tasks: BackgroundTasks):
    """Poll all pending content batches and write outbound_content to sourced_contacts.
    Runs in the background — check Slack for the completion notification, or
    query sourced_contacts.content_generated_at directly."""
    background_tasks.add_task(_content_complete_all_bg)
    return {"status": "started"}
