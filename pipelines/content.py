import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, HTTPException

from db.client import get_supabase, fetch_all
from pipelines.resource_tool import select_resource
from utils.slack import notify

_BATCH_INPUT_COST_PER_TOKEN  = 1.50 / 1_000_000
_BATCH_OUTPUT_COST_PER_TOKEN = 7.50 / 1_000_000
_BATCH_SIZE = 500

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _encode_custom_id(domain: str, email: str) -> str:
    raw = f"{domain}||{email or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _build_content_prompt(contact: dict, company: dict, resource: dict) -> str:
    return f"""You are a B2B outbound copywriter for Brevo. Generate a personalised
outbound sequence for one contact. Return everything as a single JSON object.

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

## Selected resource

- resource.company: {resource.get('company')}
- resource.title: {resource.get('title')}
- resource.type: {resource.get('type')}
- resource.industry: {resource.get('industry')}
- resource.key_metrics: {resource.get('key_metrics')}
- resource.context: {resource.get('context')}
- resource.pain_points: {resource.get('pain_points')}

---

## Global rules — apply to everything

DASHES — ABSOLUTE RULE. Zero tolerance.
  Never use em dash (—), en dash (–), or a hyphen as a
  pause or connector in any sentence in any email or
  LinkedIn content. This includes constructions like
  "X — Y", "X – Y", or "fast-growing" used as a pause.
  If you are tempted to use a dash, rewrite the sentence
  as two separate sentences or use a comma instead.
  Wrong: "They run loyalty and wallet — two systems."
  Right: "They run loyalty and wallet through two systems."
  Scan your output before returning. If you find a dash,
  rewrite that sentence.

- Casual, human tone. Write at a 5th-grade reading level.
  Slightly uncertain is better than confident and salesy.
- Never use the word "brand" or "brands"
- No exclamation marks
- Never start a sentence with "I just wanted to",
  "I know you're busy", or "I hope this finds you well"
- Do not quote input fields directly — use them as context
- You:I ratio — write more "you/your" sentences than
  "I/we/our" sentences in every email. Before outputting,
  check the ratio. If you have more I/we sentences, rewrite.
- One to two sentences per paragraph maximum.
  Write for mobile — a desktop paragraph becomes
  four lines on a phone.
- Each complete email (all paragraphs combined) must be
  75 to 125 words. Count before outputting. Cut if over.
  Email 4 must be 50 to 80 words — short is the point.
- CTA rule — the single most important rule:
  Never ask for time or a meeting in a cold email.
  Every CTA must be interest-based ("Is this on your
  radar?") or offer-based ("Worth sending over?").
  Save calendar asks for replies and active deals.
  The CTA is always the last sentence and always serves
  as the anchor text for a Lemlist template variable.
- Never generate or include URLs —
  {{cta_book_call}}, {{case_study_url}}, and {{report_url}}
  are Lemlist variables. Write only the anchor text.
- Metrics rule — never lead with ROI numbers.
  Metrics first appear in email 2 as a story element.
  They reappear in linkedin_message_2 and email 4 only.
  Email 1 and email 3 contain no metrics.
- Never pitch Brevo features as a list. Brevo appears
  once in email 1 (bridge sentence only), naturally in
  email 2, and not at all in email 3 or email 4.

---

## EMAIL 1 — Day 1 — PAS framework (Problem, Agitate, Solve)

### subject_line_1

Format rules (apply to all four subject lines):
- 2 to 6 words, all lowercase
- No punctuation except ? and —
- No first names
- No verbs as the opening word
- No superlatives or adjectives
- Must read like an internal email between colleagues,
  not a marketing email

Signal priority — pick the first that applies:

1. esp_detected is present AND is contact-based
   (Mailchimp, Klaviyo, or similar):
   → "paying per contact at [company_name]?"

2. esp_detected is present (any other ESP):
   → "[company_name]'s [esp_detected] setup"

3. has_loyalty_program is true, no ESP detected:
   → "[company_name]'s loyalty comms"

4. needs_cdp is true:
   → "fragmented data at [company_name]?"

5. email_crm_activity is present:
   → "your transactional email setup"

6. No signals available:
   → "question on your ESP"

---

### email_1_paragraph_1 — Observed signal hook

Open with something specific you noticed about them,
drawn from their signals. This is what makes it feel
researched, not templated.

Rules:
- 1 to 2 sentences
- Must be about THEM, not about Brevo
- Reference one of their signals directly as an observation:
    If esp_detected: reference the ESP by name and what
      that likely means for their sending volume at scale
      (use approximate language: "sending at volume",
      "a lot of transactional sends", "thousands of
      contacts" — never exact numbers)
    If has_loyalty_program: reference what running a
      loyalty programme at their scale means for comms
      volume (approximate language only)
    If has_wallet: reference what wallet activity implies
      about their transactional send volume
    If email_crm_activity: use it as the specific
      observation — paraphrase, never quote directly
    If no signals: use account_narrative to surface
      something specific about their communication layer
- No Brevo mention
- No metrics
- Do not open with "I noticed" or "I saw" — instead open
  with the observation itself as a statement of fact

---

### email_1_paragraph_2 — Agitate

Expand why this problem is harder than it looks for
a company like theirs.

Rules:
- 1 to 2 sentences
- Flow directly from paragraph 1
- No Brevo mention
- No metrics
- If esp_detected is present and esp_score >= 75:
    Reference esp_detected by name and the specific
    friction it creates at their scale
  If esp_detected is present and esp_score < 75:
    Reference the category of pain generically,
    not the tool name
  If esp_detected is null:
    Use account_narrative to surface the friction
    common to companies like theirs at this stage

---

### email_1_paragraph_3 — Solve (bridge only)

One sentence naming Brevo as relevant to this pain.
Then one sentence CTA — interest-based, not a meeting ask.

Rules:
- 2 sentences total, no more
- Brevo appears once, as a bridge — not a product pitch
- Shape the Brevo angle using signals:
    has_loyalty_program = true: loyalty and CRM unification
    needs_cdp = true: unified customer data view
    has_wallet = true: wallet and channel integration
    all false: email and CRM in one place
- CTA anchor text wraps {{cta_book_call}}
  Frame it as an interest question, not a meeting invite.
  Example: "Is this something on your radar this year?"
  or "Worth a conversation to see if it applies?"

---

## LINKEDIN — Day 3 — Direct message (no connection note)

### linkedin_message_1

Send directly after connecting — no note on the
connection request itself.

Rules:
- 2 to 3 sentences
- Warm, human — they just connected, treat it as such
- No Brevo mention, no meeting ask
- Open with something specific about their vertical
  or role, not a generic opener
- Always use "I work with" not "working with"
- Every sentence must have a subject and verb
- End with an open question that invites a reply,
  does not demand one

---

## EMAIL 2 — Day 7 — BAB framework (Before, After, Bridge)

### subject_line_2

Different signal from subject_line_1 — skip whichever
signal was already used. Signal priority:

1. has_loyalty_program true AND has_wallet false:
   → "loyalty + wallet — are they connected?"

2. has_wallet true:
   → "your rewards program emails"

3. needs_cdp true (if not used in subject_line_1):
   → "fragmented data at [company_name]?"

4. Default:
   → "transactional + marketing — one stack?"

---

### email_2_paragraph_1 — Before

Put company_name in the before state. This is their
current situation — the problem they are living with.

Rules:
- 1 to 2 sentences
- No Brevo mention
- No metrics yet — save them for paragraph 2
- Use account_narrative and resource.pain_points as
  context to make the before state feel accurate
- Connect their situation to resource.company naturally —
  explain the parallel without overstating it

---

### email_2_paragraph_2 — After and Bridge

Tell the case study story. Introduce the metric here
for the first time. Bridge back to company_name.

Rules:
- 3 sentences maximum
- Sentence 1: What resource.company changed (1 sentence)
- Sentence 2: The result — write one metric from
  resource.key_metrics as a narrative sentence, not
  as a stat or bullet point. "X happened, which meant Y"
  not "X% increase in Y"
- Sentence 3: CTA — offer-based, wraps {{case_study_url}}
  Example: "Worth seeing how they did it?" or
  "The full story is here if it is useful"
- Do not start this paragraph with "They"
- Brevo can be mentioned naturally in sentence 1 or 2
  as part of the story — not as a product pitch

---

## EMAIL 3 — Day 12 — New pain point + resource

This email must NOT feel like a follow-up or a
content push. It surfaces a different pain from
emails 1 and 2, then offers the resource as genuinely
useful context for that pain.

### subject_line_3

Different signal from subject_line_1 and subject_line_2 —
skip signals already used. Signal priority:

1. has_loyalty_program true AND has_wallet false
   (SMS gap angle, different from subject_line_2):
   → "loyalty + SMS — are they connected?"

2. Transactional angle (if not used in subject_line_2):
   → "your transactional email setup"

3. Default:
   → "transactional + marketing — one stack?"

---

### email_3_paragraph_1 — New pain point

Surface a pain that was NOT covered in emails 1 or 2.
Draw from signals not yet used:
- If email 1 used ESP angle: use loyalty, wallet,
  or CDP angle here
- If email 1 used loyalty: use transactional or
  deliverability angle here
- If no unused signals: use a pain common to their
  vertical drawn from account_narrative

Rules:
- 1 to 2 sentences
- Write as an observation about their situation,
  not a pitch
- No Brevo mention
- No metrics

---

### email_3_paragraph_2 — Resource as context

Connect the pain from paragraph 1 to resource.title
as something relevant, then close with an offer CTA.

Rules:
- 1 to 2 sentences
- Frame the resource as useful context for the pain,
  not as "here is a piece of content"
- Reference resource.title naturally — do not open
  with the title as the first words
- No Brevo mention
- CTA wraps {{report_url}} — offer the resource,
  not a meeting. Example: "Want me to send it over?"
  or "Happy to share the full version if useful"

---

## LINKEDIN — Day 13 — First message after connection

### linkedin_message_2

This is the first message sent after they accept the
connection — warm, not a pitch.

Rules:
- 2 to 3 sentences
- Lead with the strongest metric from resource.key_metrics
  written as a narrative sentence — "X happened for Y"
  not "X% increase"
- Connect it to company_name or vertical in one sentence
- Close with a warm open question — not a hard sell,
  not a meeting ask
- No Brevo mention

---

## EMAIL 4 — Day 18 — Breakup email

### subject_line_4

Soft close — no signals needed. Pick the most natural:
- "still open"
- "last note"
- "one more"

No first names, no punctuation, 2 words max.

---

### email_4_paragraph_1 — Binary choice

Rules:
- 1 to 2 sentences
- Acknowledge no reply without guilt or pressure
- Offer a clear binary: not a priority right now
  and I will stop, or worth a short conversation
- No Brevo mention, no features

---

### email_4_paragraph_2 — Final hook and soft close

Re-use the same metric from email 2 as the final hook,
framed as what they would be leaving on the table.
Then a soft door-open CTA.

Rules:
- 2 sentences maximum
- Sentence 1: The metric from email 2, reframed as
  an opportunity cost — "companies doing X are seeing Y"
  written as a narrative, not a stat
- Sentence 2: Soft CTA wrapping {{cta_book_call}} —
  leave the door open without pressure
  Example: "If the timing ever works, you can find
  a time here" or "Here if it ever makes sense"

---

## Output format

Return a single JSON object with exactly these keys.
No preamble, no reasoning, no markdown fences.

{{
  "subject_line_1": "",
  "email_1_paragraph_1": "",
  "email_1_paragraph_2": "",
  "email_1_paragraph_3": "",
  "linkedin_message_1": "",
  "subject_line_2": "",
  "email_2_paragraph_1": "",
  "email_2_paragraph_2": "",
  "subject_line_3": "",
  "email_3_paragraph_1": "",
  "email_3_paragraph_2": "",
  "linkedin_message_2": "",
  "subject_line_4": "",
  "email_4_paragraph_1": "",
  "email_4_paragraph_2": ""
}}"""


def _build_batch_requests(contacts: list[dict], company_map: dict) -> list[dict]:
    requests = []
    for c in contacts:
        company  = company_map.get((c["domain"], c.get("market") or ""), {})
        resource = select_resource(company)
        requests.append({
            "custom_id": _encode_custom_id(c["domain"], c.get("email") or ""),
            "params": {
                "model":      "claude-sonnet-4-6",
                "max_tokens": 4000,
                "system":     "You are a B2B copywriter. Output ONLY the raw JSON object requested. No reasoning, no analysis, no markdown fences, no preamble. Start your response with { and end with }.",
                "messages": [
                    {
                        "role":    "user",
                        "content": _build_content_prompt(c, company, resource),
                    },
                ],
            },
        })
    return requests


# ── Submit ────────────────────────────────────────────────────────────────────

async def submit_content(limit: int | None = None) -> dict:
    """
    Reads sourced_contacts with no content_generated_at, enriches with company
    context from priority_tam, submits to Claude Batch API in chunks of 500,
    and records jobs in contact_content_batches.
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
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

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
    chunks = [contacts[i : i + _BATCH_SIZE] for i in range(0, len(contacts), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(
            requests=_build_batch_requests(chunk, company_map)
        )
        mapping = {
            _encode_custom_id(c["domain"], c.get("email") or ""): {
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
            # Strip markdown fences if present anywhere in the response
            if "```" in raw_text:
                raw_text = raw_text.split("```", 1)[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.rsplit("```", 1)[0].strip()
            # Extract outermost JSON object — handles leading prose
            start = raw_text.find("{")
            end   = raw_text.rfind("}") + 1
            if start != -1 and end > start:
                raw_text = raw_text[start:end]
            content_json = json.loads(raw_text)
        except (json.JSONDecodeError, IndexError) as exc:
            logger.warning("content: failed to parse JSON for %s: %s", result.custom_id, exc)
            continue

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        updates.append({
            "id":                   meta["contact_id"],
            "outbound_content":     content_json,
            "content_batch_id":     batch_id,
            "content_generated_at": datetime.now(timezone.utc).isoformat(),
        })

    for i in range(0, len(updates), 100):
        sb.table("sourced_contacts").upsert(updates[i : i + 100], on_conflict="id").execute()

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
