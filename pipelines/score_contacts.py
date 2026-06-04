"""Daily scoring of PhantomBuster-sourced contacts via Claude Batch API.

Flow:
  1. Find unscored rows in phantombuster_contacts (scored_at IS NULL).
  2. Submit them as a single Claude Batch API request — one prompt per contact,
     scoring the job title against Brevo's ICP rubric (1-5).
  3. Poll the batch until status == "ended".
  4. Update each phantombuster_contacts row with relevance_score + reasoning + scored_at.
  5. For score >= PROMOTION_THRESHOLD, upsert into sourced_contacts (preferring
     existing Clay records, never overwriting them with PB data).
"""
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()

PROMPT_TEMPLATE = """You are a sales targeting analyst for Brevo, a CRM and marketing
automation platform for B2B and B2C companies.

Your job is to score how relevant a contact is as an outbound
target for Brevo based solely on their job title.

Brevo's ideal contacts are people who own, influence, or make
decisions about email marketing, CRM, customer communications,
marketing automation, or loyalty programmes.

Contact details:
- Job title: {title}
- Company name: {company}

Score this contact 1-5 using the following scale:

5 — Direct owner
Directly owns and operates email, CRM, marketing automation,
or loyalty platforms day-to-day.
Examples: CRM Manager, Email Marketing Manager, Head of CRM,
Marketing Automation Manager, Loyalty Manager, Head of Retention,
Lifecycle Marketing Manager, Customer Engagement Manager

4 — Strong influencer
Leads the broader marketing function and directly influences
or approves CRM/email tooling decisions.
Examples: Marketing Director, Head of Marketing, VP Marketing,
Head of Digital Marketing, CMO

3 — Adjacent influencer
Works within marketing but focus is on a related area that
occasionally intersects with email/CRM decisions.
Examples: Head of Growth, Growth Manager, Head of E-commerce,
Digital Marketing Manager, Marketing Operations Manager

2 — Weak signal
Sits within the marketing umbrella but primary focus is on
channels unrelated to email, CRM, or owned communications.
Examples: Paid Marketing Manager, SEO Manager, Social Media Manager,
Performance Marketing Manager, Brand Manager

1 — Not relevant
No connection to marketing, CRM, or customer communications.
Examples: Sales Manager, HR Director, Finance Manager, Engineer,
Operations Manager, Customer Support, Office Manager

Rules:
- Score based on the job title alone — company fit is already confirmed
- If the title is ambiguous, score based on the most likely
  interpretation of the role
- If the title is generic (e.g. "Manager", "Director") with no
  department context, score 1
- Paid, performance, and acquisition-focused titles score maximum 2
  regardless of seniority

Return your answer in this exact JSON format with no preamble, no
markdown code fences, and no text outside it:

{{
  "relevance_score": 0,
  "reasoning": ""
}}"""

MODEL = "claude-haiku-4-5-20251001"
PROMOTION_THRESHOLD = 3   # score >= 3 promotes to sourced_contacts


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(text: str) -> dict:
    """Pull the JSON object from a Claude response, stripping any code fences or prose."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def score_contacts(batch_number: int | None = None) -> dict:
    """Submit unscored phantombuster_contacts to Claude Batch API, persist scores."""
    filters: list = [("is_", "scored_at", "null")]
    if batch_number is not None:
        filters.append(("eq", "batch_number", batch_number))

    rows = fetch_all(
        "phantombuster_contacts",
        "id,domain,company_name,batch_number,job_title",
        filters=filters,
    )
    if not rows:
        logger.info("score_contacts: nothing to score")
        return {"status": "ok", "scored": 0, "promoted": 0}

    client = _client()
    reqs = []
    for r in rows:
        prompt = PROMPT_TEMPLATE.format(
            title=r.get("job_title") or "",
            company=r.get("company_name") or "",
        )
        reqs.append({
            "custom_id": f"pbc_{r['id']}",
            "params": {
                "model": MODEL,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    logger.info("score_contacts: submitting batch of %d", len(reqs))
    batch = client.messages.batches.create(requests=reqs)
    logger.info("score_contacts: batch id %s", batch.id)

    # Poll
    while True:
        b = client.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        time.sleep(10)

    # Persist scores
    sb = get_supabase()
    rows_by_id = {str(r["id"]): r for r in rows}
    scored = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    promoted_ids: list[str] = []
    for line in client.messages.batches.results(batch.id):
        if line.result.type != "succeeded":
            logger.warning("score_contacts: %s failed: %s", line.custom_id, line.result)
            continue
        contact_id = line.custom_id.replace("pbc_", "")
        parsed = _extract_json(line.result.message.content[0].text)
        score = parsed.get("relevance_score")
        reasoning = parsed.get("reasoning")
        if not isinstance(score, int):
            logger.warning("score_contacts: invalid score for %s: %s", contact_id, parsed)
            continue
        sb.table("phantombuster_contacts").update({
            "relevance_score":     score,
            "relevance_reasoning": reasoning,
            "scored_at":           now_iso,
        }).eq("id", contact_id).execute()
        scored += 1
        if score >= PROMOTION_THRESHOLD:
            promoted_ids.append(contact_id)

    promoted = _promote_to_sourced_contacts(promoted_ids)
    logger.info("score_contacts: scored=%d, promoted=%d", scored, promoted)

    return {
        "status":   "ok",
        "scored":   scored,
        "promoted": promoted,
        "batch_id": batch.id,
    }


def _promote_to_sourced_contacts(pbc_ids: list[str]) -> int:
    """Upsert each promoted PB contact into sourced_contacts. Prefers existing
    Clay-sourced records: if a (domain, email) row already exists with source='clay',
    we do NOT overwrite it. Marks promoted_to_sourced_contacts=true in either case."""
    if not pbc_ids:
        return 0
    sb = get_supabase()
    promoted = 0

    rows = fetch_all(
        "phantombuster_contacts",
        "id,domain,company_name,market,batch_number,first_name,last_name,job_title,"
        "linkedin_url,email,raw,relevance_score,relevance_reasoning",
        filters=[("in_", "id", pbc_ids)],
    )

    for r in rows:
        # Honour Clay precedence: if a Clay-sourced contact already exists, skip overwrite
        skip_upsert = False
        if r.get("email"):
            existing = sb.table("sourced_contacts").select("id,source").eq(
                "domain", r["domain"]
            ).eq("email", r["email"]).limit(1).execute().data
            if existing and existing[0].get("source") == "clay":
                skip_upsert = True

        if not skip_upsert:
            sourced_row = {
                "domain":              r["domain"],
                "company_name":        r["company_name"],
                "market":              r["market"],
                "batch_number":        r["batch_number"],
                "source":              "linkedin",
                "email":               r.get("email"),
                "first_name":          r.get("first_name"),
                "last_name":           r.get("last_name"),
                "job_title":           r.get("job_title"),
                "linkedin_url":        r.get("linkedin_url"),
                "relevance_score":     r.get("relevance_score"),
                "relevance_reasoning": r.get("relevance_reasoning"),
                "raw":                 r.get("raw"),
            }
            # If email is null we can't dedupe via (domain, email); fall back to insert
            if r.get("email"):
                sb.table("sourced_contacts").upsert(
                    sourced_row, on_conflict="domain,email"
                ).execute()
            else:
                sb.table("sourced_contacts").insert(sourced_row).execute()
            promoted += 1

        sb.table("phantombuster_contacts").update({
            "promoted_to_sourced_contacts": True,
        }).eq("id", r["id"]).execute()

    return promoted


# ── FastAPI ───────────────────────────────────────────────────────────────────

async def _run_score_bg(batch_number: int | None) -> None:
    try:
        result = score_contacts(batch_number)
        if result["scored"] > 0:
            await notify(
                f"🧠 *Contact scoring complete*\n"
                f"• Scored: {result['scored']}\n"
                f"• Promoted to sourced_contacts: {result['promoted']}"
            )
        else:
            logger.info("score_contacts: no rows to score, skipping Slack notification")
    except Exception as exc:
        await notify(f"❌ *Contact scoring failed* — `{exc}`", success=False)
        logger.exception("score_contacts: failed")


@router.post("/pipelines/score-contacts")
async def score_contacts_endpoint(background_tasks: BackgroundTasks, batch_number: int | None = None):
    """Daily cron: score all unscored phantombuster_contacts and promote score >= 3."""
    background_tasks.add_task(_run_score_bg, batch_number)
    return {"status": "started", "batch_number": batch_number}
