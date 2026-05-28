import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, HTTPException

from db.client import get_supabase, fetch_all
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


# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_content_prompt(contact: dict, company: dict) -> str:
    # ⚠️ PLACEHOLDER — replace with final prompt when ready
    # Available contact fields:
    #   first_name, last_name, job_title, seniority, linkedin_url, email
    # Available company fields:
    #   company_name, vertical, account_narrative, account_fit_score,
    #   employee_range, market, email_crm_activity, has_wallet,
    #   has_loyalty_program, needs_cdp
    #
    # Expected JSON output:
    #   {"subject": "...", "body": "...", "linkedin_note": "..."}
    raise NotImplementedError("Content prompt not yet defined — update _build_content_prompt() in pipelines/content.py")


def _build_batch_requests(contacts: list[dict]) -> list[dict]:
    return [
        {
            "custom_id": _encode_custom_id(c["domain"], c.get("email") or ""),
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": _build_content_prompt(
                            contact=c,
                            company=c.get("_company", {}),
                        ),
                    }
                ],
            },
        }
        for c in contacts
    ]


# ── Submit ────────────────────────────────────────────────────────────────────

async def submit_content(limit: int | None = None) -> dict:
    """
    Reads sourced_contacts with no content_generated_at, enriches each with
    company context from priority_tam, chunks into batches of 500, submits to
    the Claude Batch API, and records jobs in contact_content_batches.
    """
    sb = get_supabase()

    if limit:
        contacts = (
            sb.table("sourced_contacts")
            .select("id, domain, email, first_name, last_name, job_title, seniority, linkedin_url, company_name, market")
            .is_("content_generated_at", "null")
            .limit(limit)
            .execute()
            .data
        )
    else:
        contacts = fetch_all(
            "sourced_contacts",
            "id, domain, email, first_name, last_name, job_title, seniority, linkedin_url, company_name, market",
            [("is_", "content_generated_at", "null")],
        )

    if not contacts:
        logger.info("content: no contacts pending content generation")
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

    # Build a domain+market → company lookup from priority_tam
    domains = list({c["domain"] for c in contacts})
    company_rows = fetch_all(
        "priority_tam",
        "domain, market, company_name, vertical, account_narrative, account_fit_score, "
        "employee_range, email_crm_activity, has_wallet, has_loyalty_program, needs_cdp",
        [("in_", "domain", domains)],
    )
    company_map = {(r["domain"], r.get("market", "")): r for r in company_rows}

    # Attach company context to each contact
    for c in contacts:
        c["_company"] = company_map.get((c["domain"], c.get("market") or ""), {})

    client = _get_client()
    chunks = [contacts[i : i + _BATCH_SIZE] for i in range(0, len(contacts), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(requests=_build_batch_requests(chunk))
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
    """
    Checks if a content batch is complete. If so, writes outbound_subject,
    outbound_body, outbound_linkedin_note back to sourced_contacts.
    """
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

        raw_text = result.result.message.content[0].text
        try:
            # Strip markdown code fences if present
            text = raw_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(text)
        except (json.JSONDecodeError, IndexError) as exc:
            logger.warning("content: failed to parse JSON for %s: %s", result.custom_id, exc)
            continue

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        updates.append({
            "id":                     meta["contact_id"],
            "outbound_subject":       parsed.get("subject"),
            "outbound_body":          parsed.get("body"),
            "outbound_linkedin_note": parsed.get("linkedin_note"),
            "content_batch_id":       batch_id,
            "content_generated_at":   datetime.now(timezone.utc).isoformat(),
        })

    # Upsert results back to sourced_contacts in chunks of 100
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
    """
    Polls all pending contact_content_batches. When all complete, sends
    a Slack notification with totals and cost.
    """
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
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        logger.exception("content_submit: failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pipelines/content-complete-all")
async def content_complete_all():
    """Poll all pending content batches and write results to sourced_contacts."""
    try:
        return await process_all_pending_content()
    except Exception as exc:
        logger.exception("content_complete_all: failed")
        raise HTTPException(status_code=500, detail=str(exc))
