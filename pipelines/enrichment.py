import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter

from db.client import get_supabase

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

Brevo is targeting enterprise and mid-market companies (500+
employees) that run high-volume email and CRM campaigns as part of
their ABM and outbound motion.

Research the company {company_name} ({domain}) and answer the
following:

1. What does the company do and what industry are they in?

2. How many employees do they have approximately?

3. Do they likely send marketing emails or run CRM campaigns?
   (look for signs like a newsletter, promotional emails, loyalty
   programs, or customer communications)

4. Are they a good fit for Brevo? Score them 1-5 where:
   - 5 = Strong fit (500+ employees, runs high-volume email or CRM
       campaigns, clear marketing activity at scale)
   - 3 = Possible fit (some email/CRM activity but scale or need
       is unclear)
   - 1 = Poor fit (no marketing activity, too small, or no signs
       of email/CRM usage)

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

Return your answer in this exact JSON format with no preamble, no markdown
code fences, and no text outside it:

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

async def submit_enrichment() -> dict:
    """
    Reads qualified_tam_v2 rows with no account_fit_score, chunks them into
    batches of 500, submits all chunks in parallel to the Claude Batch API,
    and returns all batch IDs.
    """
    sb = get_supabase()

    rows = (
        sb.table("qualified_tam_v2")
        .select("domain, market, company_name")
        .is_("account_fit_score", "null")
        .execute()
        .data
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
            "domain, market, company_name, brevo_company_id, planhat_id, "
            "open_deals, deal_lost_date, vertical, esp_detected, esp_score, "
            "account_fit_score, account_narrative, email_crm_activity, "
            "has_wallet, has_loyalty_program, needs_cdp"
        )
        .gte("account_fit_score", 3)
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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/pipelines/enrich")
async def enrich():
    """Submits qualified_tam_v2 rows to Claude Batch API. Returns batch_ids."""
    return await submit_enrichment()


@router.post("/pipelines/enrich/complete")
async def enrich_complete(batch_id: str):
    """Processes results for a completed batch. Returns pending if not done yet."""
    return await process_results(batch_id)


@router.post("/pipelines/prioritize")
async def prioritize():
    """Promotes qualified_tam_v2 rows with fit score >= 3 into priority_tam."""
    return await run_prioritize()
