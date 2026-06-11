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
import json
import logging
import os
import re
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, HTTPException

from db.client import get_supabase, fetch_all
from pipelines.news_search import fetch_many as fetch_news_many
from pipelines.lp_generator import fetch_many as fetch_lp_many
from pipelines.resource_tool import get_all_resources
from utils.slack import notify

_BATCH_INPUT_COST_PER_TOKEN  = 1.50 / 1_000_000
_BATCH_OUTPUT_COST_PER_TOKEN = 7.50 / 1_000_000
_BATCH_SIZE = 500

# Canonical anchor text — the model is told to always write this verbatim, but
# we override server-side so a single misread by the model doesn't break the
# Lemlist link mapping.
_LP_TEASER = "Here is what your customer journey could look like with everything connected"

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
        "the Email 1 P1 rules below (esp_detected, has_loyalty_program, has_wallet, "
        "email_crm_activity, or account_narrative)."
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

## Live News
$news_instruction

## Hardcoded Resource Library
$resources_json

## Resource Selection Rules
Select TWO resources. They must always be different assets.

EMAIL 2 RESOURCE — must be a case_study. Priority (first match wins):
1. has_wallet + has_loyalty_program + hospitality/food_beverage/restaurants → buffalo-grill-repeat-visits or cafe-kitsune-loyalty
2. has_wallet + has_loyalty_program + beauty/cosmetics/wellness → loccitane-mobile-wallet
3. has_wallet + has_loyalty_program + fashion/luxury → the-kooples-mobile-wallet or jacadi-mobile-wallet
4. has_wallet + has_loyalty_program + sports/outdoor → salomon-google-wallet
5. has_wallet + has_loyalty_program + retail (generic) → jacadi-mobile-wallet
6. needs_cdp + quick_service_restaurants/food_beverage → kfc-cdp
7. needs_cdp + retail/ecommerce → oliviers-co-cdp
8. needs_cdp + fintech/payments → monisnap-automation
9. has_loyalty_program only + aviation/travel → kenya-airways-loyalty
10. has_loyalty_program only + travel/transport → suntransfers-revenue
11. Default → marketing-orchestration-benchmark-2026

EMAIL 3 RESOURCE — must be a report or ebook. Must differ from Email 2. Priority:
1. has_wallet + has_loyalty_program → mobile-wallet-loyalty-ebook
2. has_loyalty_program only → smart-loyalty-guide (preferred) or loyalty-benchmark-report
3. needs_cdp + retail → cdp-use-cases-retail
4. needs_cdp + other verticals → marketing-orchestration-benchmark-2026
5. Default → marketing-orchestration-benchmark-2026

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
- CTAs always interest-based or offer-based. NEVER ask for a meeting in a cold email. CTA is always the last sentence of the email.
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
If no news: Reference one signal as an observation about what it implies, not what it is. If esp_detected is present and esp_score >= 75, reference the ESP tool by name and what running loyalty, franchise communications, and transactional sends through it at their scale likely feels like. Approximate language only — never exact numbers. Open with the implication, not the fact. Wrong: "One Stop uses Mandrill for email." Right: "Running loyalty communications and transactional sends through Mandrill at the scale of 1,000+ stores starts to create gaps that are hard to see until something breaks."

P2 — Agitate:
Why this problem is harder than it looks for a company at their scale. 1-2 sentences. No Brevo. No metrics.
If esp_detected is present and esp_score >= 75: Reference the ESP by name and the specific friction it creates when trying to coordinate loyalty, delivery, and franchise or multi-location communications through a single transactional tool. Make them feel the gap without saying "you should switch".
If esp_detected present but esp_score < 75: Reference the category of pain generically without naming the tool.
If no ESP: Use account_narrative to surface friction common to companies like theirs at this stage.

Personalised LP teaser — sits between P2 and P3 as a standalone line. Output this in the email_1_lp_teaser field:
Always write exactly: "Here is what your customer journey could look like with everything connected"
This line never changes regardless of vertical or signals. No variable. No placeholder. Lemlist converts this line into the clickable link.

P3 — Solve:
2 sentences exactly. Sentence 1: "Brevo specialises in [specific angle drawn from signals]." Shape the angle: has_loyalty_program = coordinating loyalty and customer communications across channels; needs_cdp = unifying customer data into a single actionable view; has_wallet = connecting wallet, loyalty, and marketing channels; all false = email and CRM in one place. Sentence 2: interest-based CTA written as a single natural sentence. Never a meeting ask. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Worth a conversation about how this applies to your rollout?"

## LinkedIn 1 — Day 3
2-3 sentences. Warm, human. No Brevo. No meeting ask. Specific to their vertical or role. Use "I work with" not "working with". End with an open question.

## Email 2 — BAB — Day 7
Use your selected Email 2 case study.
Subject: Different signal from Email 1. No dashes. Options: "loyalty + wallet, are they connected?" / "your rewards programme emails" / "fragmented data at $company_name?" / "transactional + marketing, one stack?"

STRUCTURE: This email has three completely separate parts. Write each one independently. Never blend them. Never let one sentence do the work of two parts.

email_2_hook — ONE sentence only. Hard limit: 12 words maximum. This is the scroll-stopper. It names the core tension with no setup, no context, no explanation. It stands completely alone as its own visual block. The reader should feel the problem immediately without needing the paragraph below to understand it.
Good: "Most loyalty programmes live in isolation." (6 words, names the tension, stands alone)
Good: "Points accumulate. Customers still disappear." (5 words, creates a gap)
Bad: "Most retail loyalty programmes exist in isolation because customers download an app but never engage beyond the first visit." (too long, explains itself, bleeds into P1)
Bad: Any sentence that sets up or introduces the paragraph below.

email_2_paragraph_1 — 1-2 sentences. The before state. Expand on the tension from the hook — why it is real and specific for a company like theirs at their scale. Draw from account_narrative and the selected resource pain_points. Do NOT repeat or paraphrase the hook sentence. No Brevo. No metrics.

email_2_paragraph_2 — 2 sentences exactly, no more. Sentence 1: name the resource company, what they changed, and the key metric as a narrative "X happened, which meant Y" — never as a statistic or percentage standalone. Brevo can appear naturally in this sentence as part of the story. Sentence 2: offer-based CTA written as a single natural sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Just the sentence. Example: "Here is how they made the switch"

## Email 3 — Scenario + Resource — Day 12
Use your selected Email 3 report or ebook.
Subject: Different from Emails 1 and 2. Options: "loyalty + SMS, are they connected?" / "your transactional email setup" / "one thing worth seeing"

P1 — Scenario story (2-3 sentences MAX):
Drop the reader straight into a scene without any setup or preamble. Do NOT say "imagine" or "picture this". Do NOT add a contextual opener before the scene — the abruptness is intentional and breaks the pattern of a sales email. Open with a customer situation the prospect will recognise instantly from their own business. Specific to their vertical and sub-vertical. Reference their actual product or service context where possible. Shows a gap that smart engagement could close. No feature names. No Brevo. No metrics.

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
P2: 2 sentences. Sentence 1: metric from Email 2 reframed as opportunity cost, narrative form, "companies doing X are seeing Y". Sentence 2: soft door-open CTA written as a single natural sentence. This sentence IS the anchor text — Lemlist wraps it as a link. No variable. No placeholder. Leave the door open without pressure. Example: "If the timing ever works, here is a link to my calendar"

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
    """Substitute contact + company + news + resources into the master template."""
    from string import Template
    return Template(_PROMPT_TEMPLATE).safe_substitute(
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
        news_instruction     = news_instruction,
        resources_json       = resources_json,
    )


def _build_batch_requests(
    contacts: list[dict],
    company_map: dict,
    news_map: dict,
    resources_json: str,
) -> list[dict]:
    requests = []
    for c in contacts:
        company = company_map.get((c["domain"], c.get("market") or ""), {})
        domain = (c.get("domain") or "").strip().lower()
        news = news_map.get(domain, {"found": False, "usable": False})
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


def _post_process(content_json: dict, personalised_lp_url: str = "") -> dict:
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
    """
    out = dict(content_json)
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

async def submit_content(limit: int | None = None) -> dict:
    """
    Reads sourced_contacts with no content_generated_at, enriches with company
    context from priority_tam, fetches per-domain news, submits to Claude
    Batch API in chunks of 500, and records jobs in contact_content_batches.
    """
    sb = get_supabase()

    if limit:
        contacts = (
            sb.table("sourced_contacts")
            .select("id, domain, email, first_name, last_name, job_title, seniority, company_name, market, relevance_score")
            .is_("content_generated_at", "null")
            .limit(limit)
            .execute()
            .data
        )
    else:
        contacts = fetch_all(
            "sourced_contacts",
            "id, domain, email, first_name, last_name, job_title, seniority, company_name, market, relevance_score",
            [("is_", "content_generated_at", "null")],
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
        "esp_detected, esp_score",
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
            "domain":       d,
            "company_name": name,
            "industry":     company.get("vertical"),
            "market":       c.get("market") or company.get("market"),
            "esp":          company.get("esp_detected"),
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

    # Pre-serialise the resource catalogue once (same for every contact)
    resources_json = json.dumps(get_all_resources(), indent=2, ensure_ascii=False)

    client = _get_client()
    chunks = [contacts[i : i + _BATCH_SIZE] for i in range(0, len(contacts), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(
            requests=_build_batch_requests(chunk, company_map, news_map, resources_json)
        )
        mapping = {
            _encode_custom_id(c["id"]): {
                "contact_id": c["id"],
                "email":      c.get("email"),
                "domain":     c["domain"],
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
    resources_json = json.dumps(get_all_resources(), indent=2, ensure_ascii=False)
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
    return _post_process(json.loads(raw_text), personalised_lp_url=lp_url)


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

@router.post("/pipelines/content/submit")
async def content_submit(limit: int | None = None):
    """Submit sourced_contacts with no content to Claude Batch API."""
    try:
        return await submit_content(limit=limit)
    except Exception as exc:
        logger.exception("content_submit: failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pipelines/content-complete-all")
async def content_complete_all():
    """Poll all pending content batches and write outbound_content to sourced_contacts."""
    try:
        return await process_all_pending_content()
    except Exception as exc:
        logger.exception("content_complete_all: failed")
        raise HTTPException(status_code=500, detail=str(exc))
