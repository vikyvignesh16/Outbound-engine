import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter

from db.client import get_supabase, fetch_all

_BATCH_INPUT_COST_PER_TOKEN  = 1.50 / 1_000_000
_BATCH_OUTPUT_COST_PER_TOKEN = 7.50 / 1_000_000

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(company_name: str, domain: str) -> str:
    return f"""You are a sales qualification analyst for Brevo, a CRM and marketing
automation platform used by B2B and B2C companies to manage email,
SMS, and multi-channel marketing campaigns.

Brevo targets companies with 100+ employees that communicate with
customers or users through email, SMS, or CRM workflows.

Research the company {company_name} ({domain}) and answer the
following:

1. What does the company do and what industry are they in?

2. How many employees do they have approximately?

3. Do they likely send emails or manage customer communications?
   Describe what you observe — this is for context only, not scoring.
   Look for any of the following:
   - Marketing newsletters or promotional campaigns
   - Transactional emails (order confirmations, receipts, alerts)
   - Customer onboarding or lifecycle sequences
   - Loyalty or rewards programme communications
   - SMS or multi-channel customer messaging
   - B2B outreach or nurture sequences

4. Are they a good fit for Brevo? Score them 1-5 where:
   - 5 = Strong fit — 100+ employees, clear ICP match (retail,
       e-commerce, hospitality, financial services, SaaS, or any
       company with a significant customer communication layer)
   - 4 = Good fit — 100+ employees, likely sends emails or manages
       customer relationships but ICP match is slightly less clear
   - 3 = Possible fit — near the 100 employee threshold or ICP fit
       is uncertain but there are positive signals
   - 2 = Weak fit — fewer than 100 employees or very limited
       observable customer communication activity
   - 1 = Poor fit — under 50 employees, purely B2B services with
       no end-customer communication layer, or no digital presence

5. Does the company have a digital wallet or payment wallet product?
   (look for signs like a branded wallet, stored value card, prepaid
   account, or in-app payment balance)
   → has_wallet: true | false

6. Does the company run a loyalty or rewards program?
   (look for signs like a points system, membership tiers, rewards
   card, cashback scheme, or loyalty app)
   → has_loyalty_program: true | false

7. Does the company show signs of needing a Customer Data Platform?
   (look for signs like multiple customer touchpoints across channels,
   fragmented data sources, large-scale personalisation activity,
   or job postings mentioning CDP, data unification, or customer 360)
   → needs_cdp: true | false

Important: Do not assume, guess, or infer what tools, platforms, or
ESPs the company uses. Base your answer only on what you can directly
observe from their website, job postings, or public sources. If you
cannot verify something, say "unknown" for text fields and false for
boolean fields.

Return your answer in this exact JSON format with no preamble, no
markdown code fences, and no text outside it:

{{
  "response": {{
    "industry": "",
    "employees": "",
    "email_crm_activity": "",
    "fit_score": 0,
    "reasoning": "",
    "has_wallet": false,
    "has_loyalty_program": false,
    "needs_cdp": false
  }}
}}"""


# ── Batch helpers ─────────────────────────────────────────────────────────────

def _encode_custom_id(domain: str, market: str, company_name: str = "") -> str:
    raw = f"{domain}||{market}||{company_name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _decode_custom_id(custom_id: str) -> tuple[str, str]:
    """Legacy decode — only used for batches submitted before the hash-based encoding."""
    if "||" in custom_id:
        domain, market = custom_id.split("||", 1)
        return domain, market
    encoded_domain, market = custom_id.rsplit("_", 1)
    return encoded_domain.replace("_", "."), market


def build_batch_requests(companies: list[dict]) -> list[dict]:
    return [
        {
            "custom_id": _encode_custom_id(row["domain"], row["market"], row.get("company_name", "")),
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": build_prompt(row.get("company_name", ""), row["domain"]),
                    }
                ],
            },
        }
        for row in companies
    ]


_BATCH_SIZE = 500


# ── Step 5a: submit batch ─────────────────────────────────────────────────────

async def submit_enrichment(limit: int | None = None) -> dict:
    """
    Reads qualified_tam_v2 rows with no account_fit_score, chunks them into
    batches of 500, submits all chunks in parallel to the Claude Batch API,
    and returns all batch IDs. Pass limit to submit a sample batch only.
    """
    sb = get_supabase()

    if limit:
        rows = (
            sb.table("qualified_tam_v2")
            .select("domain, market, company_name")
            .is_("account_fit_score", "null")
            .limit(limit)
            .execute()
            .data
        )
    else:
        rows = fetch_all(
            "qualified_tam_v2",
            "domain, market, company_name",
            [("is_", "account_fit_score", "null")],
        )

    if not rows:
        logger.info("enrichment: no rows to enrich")
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

    client = _get_client()
    chunks = [rows[i: i + _BATCH_SIZE] for i in range(0, len(rows), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(requests=build_batch_requests(chunk))
        mapping = {
            _encode_custom_id(c["domain"], c["market"], c.get("company_name", "")): {
                "domain":       c["domain"],
                "market":       c["market"],
                "company_name": c.get("company_name", ""),
            }
            for c in chunk
        }
        sb.table("enrichment_batches").insert({
            "batch_id":            batch.id,
            "model":               "claude-sonnet-4-6",
            "status":              "pending",
            "companies_submitted": len(chunk),
            "request_mapping":     mapping,
        }).execute()
        logger.info("enrichment: submitted batch %s for %d companies", batch.id, len(chunk))
        return batch.id

    batch_ids = await asyncio.gather(*[submit_chunk(c) for c in chunks])
    logger.info("enrichment: %d batches submitted, %d companies total", len(batch_ids), len(rows))
    return {"status": "ok", "submitted": len(rows), "batches": len(batch_ids), "batch_ids": list(batch_ids)}


# ── Step 5b: process results ──────────────────────────────────────────────────

async def process_results(batch_id: str) -> dict:
    """
    Checks if the batch is complete. If not, returns {"status": "pending"}.
    If complete, parses results and upserts account_fit_score + signal fields
    into qualified_tam_v2.
    """
    client = _get_client()
    batch = await client.messages.batches.retrieve(batch_id)

    if batch.processing_status != "ended":
        return {"status": "pending", "batch_id": batch_id}

    sb = get_supabase()

    batch_row = (
        sb.table("enrichment_batches")
        .select("request_mapping")
        .eq("batch_id", batch_id)
        .execute()
        .data
    )
    request_mapping: dict = batch_row[0]["request_mapping"] if batch_row else {}

    updates = []
    total_input = 0
    total_output = 0

    async for result in await client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            logger.warning(
                "enrichment: skipping %s result for %s",
                result.result.type, result.custom_id,
            )
            continue
        try:
            text = result.result.message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)["response"]
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.error("enrichment: parse error for %s: %s", result.custom_id, exc)
            continue

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        company_info = request_mapping.get(result.custom_id)
        if company_info is not None:
            domain       = company_info["domain"]
            market       = company_info["market"]
            company_name = company_info.get("company_name", "")
        else:
            # Legacy batch submitted before hash-based encoding — fall back to decode
            try:
                domain, market = _decode_custom_id(result.custom_id)
                company_name = ""
            except Exception:
                logger.warning("enrichment: cannot resolve custom_id %s — skipping", result.custom_id)
                continue

        updates.append({
            "domain":              domain,
            "market":              market,
            "company_name":        company_name,
            "account_fit_score":   data.get("fit_score"),
            "vertical":            data.get("industry"),
            "account_narrative":   data.get("reasoning"),
            "email_crm_activity":  data.get("email_crm_activity"),
            "has_wallet":          data.get("has_wallet", False),
            "has_loyalty_program": data.get("has_loyalty_program", False),
            "needs_cdp":           data.get("needs_cdp", False),
        })

    for i in range(0, len(updates), 100):
        chunk = updates[i : i + 100]
        sb.table("qualified_tam_v2").upsert(chunk, on_conflict="domain,market,company_name").execute()

    cost = (total_input * _BATCH_INPUT_COST_PER_TOKEN
          + total_output * _BATCH_OUTPUT_COST_PER_TOKEN)

    sb.table("enrichment_batches").update({
        "status":             "completed",
        "companies_enriched": len(updates),
        "input_tokens":       total_input,
        "output_tokens":      total_output,
        "estimated_cost_usd": round(cost, 6),
        "completed_at":       datetime.now(timezone.utc).isoformat(),
    }).eq("batch_id", batch_id).execute()

    logger.info("enrichment: wrote %d results from batch %s (cost: $%.6f)", len(updates), batch_id, cost)
    return {
        "status":              "ok",
        "enriched":            len(updates),
        "input_tokens":        total_input,
        "output_tokens":       total_output,
        "estimated_cost_usd":  round(cost, 6),
    }


# ── Step 6: Prioritize ────────────────────────────────────────────────────────

async def run_prioritize() -> dict:
    """
    Reads all rows from qualified_tam_v2 with account_fit_score >= 3 and
    upserts them into priority_tam. Called after all enrichment batches complete.
    """
    sb = get_supabase()

    rows = (
        sb.table("qualified_tam_v2")
        .select(
            "domain, market, company_name, company_type, employee_range, "
            "location, country, linkedin_url, vertical, "
            "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
            "esp_detected, esp_score, account_fit_score, account_narrative, "
            "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp"
        )
        .gte("account_fit_score", 3)
        .limit(100000)
        .execute()
        .data
    )

    if not rows:
        logger.info("prioritize: no qualifying rows")
        return {"status": "ok", "prioritized": 0}

    for i in range(0, len(rows), 100):
        chunk = rows[i : i + 100]
        sb.table("priority_tam").upsert(chunk, on_conflict="domain,market,company_name").execute()

    logger.info("prioritize: upserted %d rows into priority_tam", len(rows))
    return {"status": "ok", "prioritized": len(rows)}


# ── Step 5c: poll all pending batches ────────────────────────────────────────

async def process_all_pending() -> dict:
    """
    Polls all pending enrichment batches.
    If any are still processing, returns still_pending count.
    Once all complete, runs prioritize then dbt tests.
    """
    from pipelines.dbt_runner import run_dbt_tests
    from utils.slack import notify

    try:
        sb = get_supabase()

        pending = (
            sb.table("enrichment_batches")
            .select("batch_id")
            .eq("status", "pending")
            .execute()
            .data
        )

        if not pending:
            return {
                "status": "ok",
                "message": "no_pending_batches",
                "processed": 0,
                "still_pending": 0,
                "prioritize": None,
                "dbt": None,
            }

        still_pending = 0
        total_enriched = 0

        for row in pending:
            result = await process_results(row["batch_id"])
            if result["status"] == "pending":
                still_pending += 1
            else:
                total_enriched += result.get("enriched", 0)

        if still_pending > 0:
            return {
                "status":         "ok",
                "processed":      len(pending) - still_pending,
                "still_pending":  still_pending,
                "total_enriched": total_enriched,
                "prioritize":     None,
                "dbt":            None,
            }

        # All batches done — run prioritize then dbt
        prioritize_result = await run_prioritize()
        dbt_result = run_dbt_tests()

        # Build score + ESP breakdown from DB
        score_rows = (
            sb.table("qualified_tam_v2")
            .select("account_fit_score")
            .not_.is_("account_fit_score", "null")
            .execute()
            .data
        )
        from collections import Counter
        score_counts = Counter(r["account_fit_score"] for r in score_rows)
        score_line = " | ".join(f"{s}★ {score_counts[s]}" for s in sorted(score_counts, reverse=True))

        esp_rows = (
            sb.table("qualified_tam_v2")
            .select("esp_detected")
            .not_.is_("esp_detected", "null")
            .execute()
            .data
        )
        esp_counts = Counter(r["esp_detected"] for r in esp_rows)
        top_esp = sorted(esp_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        esp_line = " | ".join(f"{e} {c}" for e, c in top_esp)

        dbt_status = "✅ passed" if dbt_result["passed"] else "❌ failed"
        await notify(
            f"✅ *Enrichment complete*\n"
            f"• Enriched: {total_enriched} companies\n"
            f"• Fit scores: {score_line}\n"
            f"• ESP detected: {esp_line or 'none'}\n"
            f"• Priority TAM: {prioritize_result['prioritized']} companies pushed\n"
            f"• dbt: {dbt_status}"
        )

        return {
            "status":         "ok",
            "processed":      len(pending),
            "still_pending":  0,
            "total_enriched": total_enriched,
            "prioritize":     prioritize_result,
            "dbt":            dbt_result,
        }

    except Exception as exc:
        await notify(f"❌ *Enrich poller failed* — `{exc}`", success=False)
        raise


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/pipelines/enrich")
async def enrich(limit: int | None = None):
    """Submits qualified_tam_v2 rows to Claude Batch API. Pass ?limit=100 for a sample run."""
    return await submit_enrichment(limit=limit)


@router.post("/pipelines/enrich/complete")
async def enrich_complete(batch_id: str):
    """Processes results for a completed batch. Returns pending if not done yet."""
    return await process_results(batch_id)


@router.post("/pipelines/enrich-complete-all")
async def enrich_complete_all():
    """Polls all pending batches. Runs prioritize + dbt once all are done."""
    return await process_all_pending()


@router.post("/pipelines/prioritize")
async def prioritize():
    """Promotes qualified_tam_v2 rows with fit score >= 3 into priority_tam."""
    return await run_prioritize()
