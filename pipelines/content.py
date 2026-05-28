import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks, HTTPException

from db.client import get_supabase, fetch_all
from utils.slack import notify

# Standard API pricing (not Batch)
_INPUT_COST_PER_TOKEN  = 3.00 / 1_000_000
_OUTPUT_COST_PER_TOKEN = 15.00 / 1_000_000
_CONCURRENCY = 5

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _get_resource(vertical: str, has_loyalty: bool, needs_cdp: bool, has_wallet: bool) -> dict:
    # ⚠️ PENDING: implement pipelines/resource_tool.py
    # resource = search_brevo_resources(vertical, has_loyalty, needs_cdp, has_wallet)
    return {}


def _build_content_prompt(contact: dict, company: dict, resource: dict) -> str:
    return f"""You are an expert B2B outbound copywriter for Brevo, a CRM and
marketing automation platform. Your job is to generate personalised
outbound sequence content for a specific contact. You will generate
all content in one pass and return it as a single JSON object.

You write in a conversational but professional tone. Every piece of
content must feel like it was written specifically for this person
and company — not like a mass email sequence.

---

## Contact and company data

- first_name: {contact.get('first_name', '')}
- job_title: {contact.get('job_title', '')}
- company_name: {company.get('company_name') or contact.get('company_name', '')}
- vertical: {company.get('vertical', '')}
- esp_detected: {company.get('esp_detected', 'unknown')}
- esp_score: {company.get('esp_score', 0)}
- email_crm_activity: {company.get('email_crm_activity', '')}
- account_narrative: {company.get('account_narrative', '')}
- relevance_score: {company.get('account_fit_score', 3)}
- has_loyalty_program: {company.get('has_loyalty_program', False)}
- needs_cdp: {company.get('needs_cdp', False)}
- has_wallet: {company.get('has_wallet', False)}

## Resource data (retrieved by tool)

- resource.company: {resource.get('company', '')}
- resource.title: {resource.get('title', '')}
- resource.type: {resource.get('type', '')}
- resource.industry: {resource.get('industry', '')}
- resource.key_metrics: {resource.get('key_metrics', '')}
- resource.context: {resource.get('context', '')}
- resource.pain_points: {resource.get('pain_points', '')}
- resource.brevo_features_tags: {resource.get('brevo_features_tags', '')}

---

## Global rules — apply to every piece of content

- Conversational but professional tone throughout
- Never use the word "brand" or "brands" — use "company",
  "organisation", or "team"
- No exclamation marks anywhere
- Never start a sentence with "I just wanted to" or
  "I know you're busy" or "I hope this finds you well"
- Do not quote input fields directly — use them as context
  to inform the writing
- Every paragraph must flow naturally from the previous one
  within the same email — read what came before before writing
- Never mention Brevo features as a list — weave them
  naturally into sentences
- The CTA is always a hyperlink — the closing sentence of
  each email and the closing line of email 4 paragraph 2
  serves as the anchor text for {{cta_book_call}}
  Write it as a natural sentence that makes clicking
  feel like the obvious next step

---

## EMAIL 1 — Day 1 — Pain point email

### subject_line_1

Generate a subject line using the following logic:

If relevance_score = 5:
  Write a pure curiosity subject line.
  Do not mention the ESP, role, or vertical explicitly.
  Make it intriguing enough to open without revealing
  the pitch.

If relevance_score = 4 AND esp_score >= 75
AND esp_detected is not null:
  Write a subject line that references esp_detected
  by name. Imply they might be outgrowing it or that
  something has changed.

If relevance_score = 4 AND (esp_score < 75
OR esp_detected is null):
  Write a subject line that references their job
  function in vertical. Do not use their exact job
  title — imply the role.

If relevance_score = 3:
  Write a subject line that references vertical
  specifically. Frame it as something shifting or
  worth paying attention to in their industry.

Rules:
- Maximum 6 words
- No exclamation marks
- No clickbait phrasing
- Conversational not salesy
- Always end with a sense of curiosity or open question

---

### email_1_paragraph_1

Generate the opening paragraph of email 1.

Rules:
- 2-3 sentences maximum
- Must feel specific to this person and company
- Reference their role and company naturally — do not
  start with "As a [job title]"
- If email_crm_activity contains useful detail, reference
  it naturally without making it obvious it was researched
- If email_crm_activity is empty or vague, lean on
  vertical and job_title instead
- Do not mention Brevo in this paragraph
- This is an observation not a pitch
- Never use the word "brand" or "brands"

---

### email_1_paragraph_2

Generate the second paragraph of email 1.
This paragraph expands the pain point from paragraph 1.

Rules:
- 2-3 sentences maximum
- Must flow directly from email_1_paragraph_1 — pick up
  where paragraph 1 left off, do not reintroduce the
  company or role
- Do not mention Brevo in this paragraph
- This paragraph is about their problem not your solution

If esp_detected is present and esp_score >= 75:
  Reference esp_detected by name and describe the
  specific limitations it creates at scale for a
  vertical company

If esp_detected is present and esp_score < 75:
  Reference their email setup generically without
  naming the tool — focus on the category of pain

If esp_detected is null:
  Focus entirely on the pain point common to vertical
  companies at this stage — use account_narrative
  as context

---

### email_1_paragraph_3

Generate the third paragraph of email 1.
This is the bridge paragraph — first mention of Brevo.

Rules:
- 2-3 sentences maximum
- Must flow directly from email_1_paragraph_2
- This is the first and only mention of Brevo in email 1
- Do not list features or make it sound like a product page
- Frame Brevo as relevant to the pain raised in paragraphs
  1 and 2 — not as a generic platform pitch
- Use boolean signals to shape the Brevo angle:
    If has_loyalty_program = true:
      Lead with Brevo's loyalty and email integration angle
    If needs_cdp = true:
      Lead with Brevo's data platform and unified
      customer view angle
    If has_wallet = true:
      Lead with Brevo's wallet and CRM integration angle
    If all false:
      Lead with Brevo's email and CRM unification angle
- Keep tone warm and confident — not pushy
- End with a sentence that naturally leads into the CTA
  and serves as the anchor text for the booking link —
  something like "Happy to walk you through how we've
  approached this" or similar warm open door

---

## LINKEDIN — Day 3 — Connection request

### linkedin_connection_note

Generate a LinkedIn connection request note.

Rules:
- Hard limit of 300 characters including spaces —
  do not exceed this under any circumstances
- Do not reference any email sent — standalone touchpoint
- Do not mention Brevo by name
- Do not mention features or products
- Open with a hook — something specific to their vertical,
  role, or a pattern observed — not a generic opener
- Use resource.company or vertical as a relevance signal
  if it fits naturally
- Use account_narrative as background context to sharpen
  the hook — do not quote directly
- No exclamation marks
- Conversational and human — should not read as automated
- Count characters before outputting — must be under 300

---

## LINKEDIN — Day 3+1 — First message after connection accepted

### linkedin_message_1

Generate the first LinkedIn direct message sent one day
after the connection request is accepted.

Rules:
- 2-3 sentences maximum
- Warm and conversational — this person just accepted
  your connection, treat it as a human moment
- Do not pitch Brevo by name or mention any features
- Do not ask for a meeting or call in this message
- Open with a natural thank you for connecting — but
  pair it immediately with something specific
- Reference vertical or resource.company as a relevance
  signal — shows you work in their space
- Use account_narrative as background context — do not
  quote directly
- End with an open door that invites a reply without
  demanding one
- No exclamation marks
- Should feel like a message a thoughtful person wrote

---

## EMAIL 2 — Day 7 — Case study email

### subject_line_2

Generate the subject line for email 2.

If resource.industry matches vertical closely:
  Use resource.company name + headline metric from
  resource.key_metrics as the angle

If resource.industry is adjacent but not exact match:
  Use the metric only — drop the company name

If resource.key_metrics is empty or weak:
  Use a curiosity angle referencing vertical only

Rules:
- Maximum 6 words
- No exclamation marks
- No clickbait phrasing
- Never start with "How to"
- Conversational not salesy

---

### email_2_paragraph_1

Generate the opening paragraph of email 2.
This paragraph connects their situation to the resource.

Rules:
- 2-3 sentences maximum
- Do not open with "I wanted to share" or "I thought
  you might find this interesting" — start specific
- Connect company_name's situation to resource.company
  in a way that feels earned — explain why they are
  comparable without overstating it
- Use account_narrative as context to find the connection
- Use resource.context to understand what resource.company
  was dealing with — do not quote directly
- Match tone of email_1_paragraph_1 for consistency
- Do not mention Brevo in this paragraph
- Do not reveal the metrics yet

---

### email_2_paragraph_2

Generate the second and final body paragraph of email 2.
This paragraph tells the case study story.

Rules:
- 3-4 sentences maximum
- Must flow directly from email_2_paragraph_1
- No reintroduction of the case study company
- Tell the story in this order:
    1. What resource.company was dealing with — 1 sentence
    2. What changed and what the results were — 1-2
       sentences, written as narrative not bullet points
    3. How Brevo made it possible — 1 sentence
- End with a sentence connecting the story back to
  company_name — make it feel relevant not forced
- This closing sentence leads naturally into the CTA
  and serves as the anchor text for the booking link
- Do not start this paragraph with "They"

---

## EMAIL 3 — Day 12 — Report email

### subject_line_3

Generate the subject line for email 3.

If resource.type is report or benchmark:
  Lead with a data or finding angle — make it feel
  like there is a specific number worth knowing

If resource.type is ebook or guide:
  Lead with an outcome or practical theme relevant
  to vertical and job_title

If neither applies:
  Use a curiosity angle referencing vertical

Rules:
- Maximum 6 words
- No exclamation marks
- No clickbait
- Never start with "How to"

---

### email_3_paragraph_1

Generate the single body paragraph of email 3.
This paragraph must do everything in one — hook,
content reference, key finding, and CTA lead-in.

Rules:
- 3-4 sentences maximum
- Should feel like a colleague sharing something
  useful — not a marketing email pushing content
- Reference resource.title naturally — do not open
  with the title as the first words
- Make relevance to vertical and job_title clear
  without being heavy handed
- Include one specific finding or stat from
  resource.context — written as a sentence, not
  a bullet point, not quoted directly
- Use account_narrative as context — do not quote
- End with a sentence that naturally leads into the
  CTA and serves as the anchor text for the booking
  link — make the conversation feel like the obvious
  next step
- Match tone of email_1_paragraph_1 for consistency

---

## LINKEDIN — Day 13 — Second LinkedIn message

### linkedin_message_2

Generate the second and final LinkedIn direct message.
This message leads with a metric and closes with a hook.

Rules:
- 2-3 sentences maximum
- Lead with the strongest metric from
  resource.key_metrics — write it as a sentence,
  not a stat, not a bullet point
- Connect the metric to company_name or vertical
  in one sentence — make it feel relevant
- Close with a direct but warm hook — an open
  question or soft invitation, not a hard sell
- Do not mention Brevo by name
- Do not repeat anything from linkedin_message_1
- No exclamation marks
- Should feel like the natural last thing a
  thoughtful person would say

---

## EMAIL 4 — Day 18 — Breakup email

### subject_line_4

Generate the subject line for email 4.

Rules:
- Maximum 6 words
- Soft, warm and human — not passive aggressive
- No guilt-tripping language
- Can use first_name if it fits naturally
- Creates just enough warmth or curiosity to get
  the open without overpromising

---

### email_4_paragraph_1

Generate the first paragraph of email 4.
This is the breakup email — warm acknowledgement
and binary choice.

Rules:
- 2-3 sentences maximum
- Acknowledge no reply warmly — no guilt, no pressure
- Offer a clear binary choice — not a priority right
  now and I will stop, or worth a conversation
- Do not pitch Brevo or any feature
- Do not reference any specific email from the sequence
- Do not start with "I just wanted to" or "I know
  you're busy"
- Keep it human — should feel like a person wrote it

---

### email_4_paragraph_2

Generate the second and final paragraph of email 4.
This paragraph lands one last hook before the soft close.

Rules:
- 2-3 sentences maximum
- Must flow directly from email_4_paragraph_1
- Land one final hook — choose the strongest signal:
    If resource.key_metrics is strong:
      Reference the case study result as the hook —
      one compelling number or outcome written as
      a sentence not a stat
    If resource.key_metrics is weak or empty:
      Use a vertical observation as the hook —
      something about what is shifting in the industry
- Do not repitch Brevo features or products
- End with a warm sentence that leaves the door open
  and serves as the anchor text for the booking link
- Should feel like the last thing a thoughtful
  salesperson would say — not a desperate last push

---

## Output format

Return your response as a single JSON object with exactly
these keys and no other text, no preamble, no markdown
code fences:

{{
  "subject_line_1": "",
  "email_1_paragraph_1": "",
  "email_1_paragraph_2": "",
  "email_1_paragraph_3": "",
  "linkedin_connection_note": "",
  "linkedin_message_1": "",
  "subject_line_2": "",
  "email_2_paragraph_1": "",
  "email_2_paragraph_2": "",
  "subject_line_3": "",
  "email_3_paragraph_1": "",
  "linkedin_message_2": "",
  "subject_line_4": "",
  "email_4_paragraph_1": "",
  "email_4_paragraph_2": ""
}}"""


# ── Process single contact ─────────────────────────────────────────────────────

async def _process_one(
    client: anthropic.AsyncAnthropic,
    semaphore: asyncio.Semaphore,
    sb,
    contact: dict,
    company: dict,
    resource: dict,
) -> tuple[bool, int, int]:
    """Returns (success, input_tokens, output_tokens)."""
    async with semaphore:
        try:
            prompt = _build_content_prompt(contact, company, resource)
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            content_json = json.loads(text)

            sb.table("sourced_contacts").update({
                "outbound_content":      content_json,
                "content_generated_at":  datetime.now(timezone.utc).isoformat(),
            }).eq("id", contact["id"]).execute()

            return True, response.usage.input_tokens, response.usage.output_tokens

        except Exception as exc:
            logger.warning("content: failed for contact %s (%s): %s", contact["id"], contact.get("email"), exc)
            return False, 0, 0


# ── Main submit function ──────────────────────────────────────────────────────

async def submit_content(limit: int | None = None) -> dict:
    """
    Reads sourced_contacts with no outbound_content, fetches company context
    from priority_tam, generates content via standard Claude API with
    controlled concurrency, and writes outbound_content jsonb back.
    """
    sb = get_supabase()

    if limit:
        contacts = (
            sb.table("sourced_contacts")
            .select("id, domain, email, first_name, last_name, job_title, seniority, company_name, market")
            .is_("content_generated_at", "null")
            .limit(limit)
            .execute()
            .data
        )
    else:
        contacts = fetch_all(
            "sourced_contacts",
            "id, domain, email, first_name, last_name, job_title, seniority, company_name, market",
            [("is_", "content_generated_at", "null")],
        )

    if not contacts:
        logger.info("content: no contacts pending generation")
        return {"status": "ok", "submitted": 0, "processed": 0, "errors": 0}

    # Build domain+market → company context from priority_tam
    domains = list({c["domain"] for c in contacts})
    company_rows = fetch_all(
        "priority_tam",
        "domain, market, company_name, vertical, account_narrative, account_fit_score, "
        "employee_range, email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "esp_detected, esp_score",
        [("in_", "domain", domains)],
    )
    company_map = {(r["domain"], r.get("market", "")): r for r in company_rows}

    client = _get_client()
    semaphore = asyncio.Semaphore(_CONCURRENCY)

    # Track this run in contact_content_batches
    run_id = str(uuid.uuid4())
    sb.table("contact_content_batches").insert({
        "batch_id":           run_id,
        "model":              "claude-sonnet-4-6",
        "status":             "pending",
        "contacts_submitted": len(contacts),
    }).execute()

    tasks = []
    for c in contacts:
        company = company_map.get((c["domain"], c.get("market") or ""), {})
        resource = _get_resource(
            vertical=company.get("vertical", ""),
            has_loyalty=company.get("has_loyalty_program", False),
            needs_cdp=company.get("needs_cdp", False),
            has_wallet=company.get("has_wallet", False),
        )
        tasks.append(_process_one(client, semaphore, sb, c, company, resource))

    results = await asyncio.gather(*tasks)

    successes  = sum(1 for ok, _, _ in results if ok)
    errors     = len(results) - successes
    total_in   = sum(i for _, i, _ in results)
    total_out  = sum(o for _, _, o in results)
    cost       = total_in * _INPUT_COST_PER_TOKEN + total_out * _OUTPUT_COST_PER_TOKEN

    sb.table("contact_content_batches").update({
        "status":             "completed",
        "contacts_completed": successes,
        "input_tokens":       total_in,
        "output_tokens":      total_out,
        "estimated_cost_usd": round(cost, 6),
        "completed_at":       datetime.now(timezone.utc).isoformat(),
    }).eq("batch_id", run_id).execute()

    logger.info(
        "content: %d/%d contacts generated — $%.4f",
        successes, len(contacts), cost,
    )
    return {
        "status":             "ok",
        "processed":          successes,
        "errors":             errors,
        "input_tokens":       total_in,
        "output_tokens":      total_out,
        "estimated_cost_usd": round(cost, 4),
    }


async def _run_content_bg(limit: int | None = None) -> None:
    try:
        result = await submit_content(limit=limit)
        if result["processed"] > 0:
            await notify(
                f"✅ *Content generation complete*\n"
                f"• Generated: {result['processed']} contacts\n"
                f"• Errors: {result['errors']}\n"
                f"• Estimated cost: ${result['estimated_cost_usd']:.4f}"
            )
    except Exception as exc:
        await notify(f"❌ *Content generation failed* — `{exc}`", success=False)
        logger.exception("content: background run failed")
        raise


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/pipelines/content/submit")
async def content_submit(background_tasks: BackgroundTasks, limit: int | None = None):
    """Generate outbound sequence content for all contacts with no content_generated_at."""
    background_tasks.add_task(_run_content_bg, limit=limit)
    return {"status": "started"}


@router.post("/pipelines/content-complete-all")
async def content_complete_all(background_tasks: BackgroundTasks):
    """Alias for /pipelines/content/submit — processes all pending contacts."""
    background_tasks.add_task(_run_content_bg)
    return {"status": "started"}
