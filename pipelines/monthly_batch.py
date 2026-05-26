import asyncio
import logging
import os
from datetime import date

import httpx
from fastapi import APIRouter, HTTPException

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

BATCH_LIMIT = 1000

# Maps individual market codes → Clay webhook env var key.
# DACH markets (DE, AT, CH) share one webhook.
MARKET_TO_WEBHOOK_KEY: dict[str, str] = {
    "UK": "CLAY_WEBHOOK_UK",
    "DE": "CLAY_WEBHOOK_DACH",
    "AT": "CLAY_WEBHOOK_DACH",
    "CH": "CLAY_WEBHOOK_DACH",
}


async def run_monthly_batch() -> dict:
    """
    Selects the next BATCH_LIMIT never-contacted companies from priority_tam,
    ordered by account_fit_score DESC then prioritized_at ASC, and inserts
    them into campaign_batches with an auto-incrementing batch_number.
    """
    sb = get_supabase()

    existing = (
        sb.table("campaign_batches")
        .select("domain, market, batch_number")
        .execute()
        .data
    )
    contacted = {(r["domain"], r["market"]) for r in existing}
    next_batch_number = max((r["batch_number"] for r in existing), default=0) + 1

    candidates = (
        sb.table("priority_tam")
        .select("domain, market, company_name, account_fit_score, vertical")
        .order("account_fit_score", desc=True)
        .order("prioritized_at", desc=False)
        .execute()
        .data
    )

    batch_month = date.today().replace(day=1).isoformat()
    selected = [
        {**row, "batch_number": next_batch_number, "batch_month": batch_month}
        for row in candidates
        if (row["domain"], row["market"]) not in contacted
    ][:BATCH_LIMIT]

    if not selected:
        logger.info("monthly_batch: no new candidates to select")
        return {"status": "ok", "selected": 0, "batch_number": next_batch_number, "batch_month": batch_month}

    for i in range(0, len(selected), 100):
        sb.table("campaign_batches").insert(selected[i : i + 100]).execute()

    logger.info(
        "monthly_batch: inserted %d companies as batch #%d (%s)",
        len(selected), next_batch_number, batch_month,
    )
    return {
        "status":       "ok",
        "selected":     len(selected),
        "batch_number": next_batch_number,
        "batch_month":  batch_month,
    }


async def push_batch_to_clay(batch_number: int) -> dict:
    """
    Reads campaign_batches for the given batch_number, groups by market,
    and POSTs each group to the corresponding CLAY_WEBHOOK_{MARKET} env var URL.
    Markets with no webhook configured are skipped with a warning.
    """
    sb = get_supabase()

    rows = (
        sb.table("campaign_batches")
        .select("domain, market, company_name, account_fit_score, vertical, batch_month")
        .eq("batch_number", batch_number)
        .execute()
        .data
    )

    if not rows:
        raise HTTPException(status_code=404, detail=f"No companies found for batch_number={batch_number}")

    # Group by webhook key so DACH markets (DE, AT, CH) merge into one POST
    by_webhook: dict[str, list] = {}
    for row in rows:
        key = MARKET_TO_WEBHOOK_KEY.get(row["market"], f"CLAY_WEBHOOK_{row['market'].upper()}")
        by_webhook.setdefault(key, []).append(row)

    results = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def push_group(webhook_key: str, companies: list) -> None:
            webhook_url = os.environ.get(webhook_key)
            if not webhook_url:
                logger.warning("monthly_batch: %s not configured — skipping %d companies", webhook_key, len(companies))
                results[webhook_key] = {"status": "skipped", "reason": "no_webhook_configured", "companies": len(companies)}
                return
            resp = await client.post(webhook_url, json=companies)
            resp.raise_for_status()
            logger.info("monthly_batch: pushed %d companies via %s", len(companies), webhook_key)
            results[webhook_key] = {"status": "ok", "companies": len(companies)}

        await asyncio.gather(*[push_group(k, c) for k, c in by_webhook.items()])

    return {"status": "ok", "batch_number": batch_number, "webhooks": results}


@router.post("/pipelines/monthly-batch")
async def monthly_batch():
    """Selects next 1000 uncontacted priority companies and logs them to campaign_batches."""
    return await run_monthly_batch()


@router.post("/pipelines/monthly-batch/push")
async def monthly_batch_push(batch_number: int):
    """Pushes a campaign batch to Clay webhooks, grouped by market."""
    return await push_batch_to_clay(batch_number)
