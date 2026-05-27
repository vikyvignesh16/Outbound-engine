import asyncio
import logging
import os
from datetime import date

import httpx
from fastapi import APIRouter, HTTPException

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

UK_LIMIT     = 500
DACH_LIMIT   = 500
DACH_MARKETS = {"DE", "AT", "CH"}

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
        .select("domain, market, company_name, batch_number")
        .execute()
        .data
    )
    contacted = {(r["domain"], r["market"], r["company_name"]) for r in existing}
    next_batch_number = max((r["batch_number"] for r in existing), default=0) + 1

    candidates = (
        sb.table("priority_tam")
        .select(
            "domain, market, company_name, company_type, employee_range, "
            "location, country, linkedin_url, vertical, "
            "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
            "esp_detected, esp_score, account_fit_score, account_narrative, "
            "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp"
        )
        .order("account_fit_score", desc=True)
        .order("prioritized_at", desc=False)
        .execute()
        .data
    )

    batch_month = date.today().replace(day=1).isoformat()

    uk_selected = [
        {**row, "batch_number": next_batch_number, "batch_month": batch_month}
        for row in candidates
        if row["market"] == "UK"
        and (row["domain"], row["market"], row["company_name"]) not in contacted
    ][:UK_LIMIT]

    dach_selected = [
        {**row, "batch_number": next_batch_number, "batch_month": batch_month}
        for row in candidates
        if row["market"] in DACH_MARKETS
        and (row["domain"], row["market"], row["company_name"]) not in contacted
    ][:DACH_LIMIT]

    selected = uk_selected + dach_selected

    if not selected:
        logger.info("monthly_batch: no new candidates to select")
        return {
            "status": "ok", "selected": 0,
            "uk_selected": 0, "dach_selected": 0,
            "batch_number": next_batch_number, "batch_month": batch_month,
        }

    for i in range(0, len(selected), 100):
        sb.table("campaign_batches").insert(selected[i : i + 100]).execute()

    logger.info(
        "monthly_batch: inserted %d companies as batch #%d (%s) — UK=%d DACH=%d",
        len(selected), next_batch_number, batch_month, len(uk_selected), len(dach_selected),
    )
    return {
        "status":        "ok",
        "selected":      len(selected),
        "uk_selected":   len(uk_selected),
        "dach_selected": len(dach_selected),
        "batch_number":  next_batch_number,
        "batch_month":   batch_month,
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
        .select(
            "domain, market, company_name, company_type, employee_range, "
            "location, country, linkedin_url, vertical, "
            "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
            "esp_detected, esp_score, account_fit_score, account_narrative, "
            "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
            "batch_month"
        )
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
            for company in companies:
                resp = await client.post(webhook_url, json=company)
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


@router.post("/pipelines/run-monthly")
async def run_monthly():
    """1st-of-month cron: select campaign batch then run dbt tests."""
    from pipelines.dbt_runner import run_dbt_tests
    from utils.slack import notify
    try:
        batch_result = await run_monthly_batch()
        dbt_result = run_dbt_tests()
        dbt_status = "✅ passed" if dbt_result["passed"] else "❌ failed"
        await notify(
            f"✅ *Monthly batch* — batch #{batch_result['batch_number']}, "
            f"UK={batch_result['uk_selected']} DACH={batch_result['dach_selected']}, dbt {dbt_status}"
        )
        return {"batch": batch_result, "dbt": dbt_result}
    except Exception as exc:
        await notify(f"❌ *Monthly batch failed* — `{exc}`", success=False)
        raise
