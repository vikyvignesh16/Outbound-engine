import asyncio
import logging
import os
from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException

from db.client import get_supabase, fetch_all
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()

UK_LIMIT     = 500
DACH_LIMIT   = 500
UKI_MARKETS  = {"UK", "Ireland"}
DACH_MARKETS = {"DE", "AT", "CH"}

MARKET_TO_WEBHOOK_KEY: dict[str, str] = {
    "UK":      "CLAY_WEBHOOK_UK",
    "Ireland": "CLAY_WEBHOOK_UK",
    "DE":      "CLAY_WEBHOOK_DACH",
    "AT":      "CLAY_WEBHOOK_DACH",
    "CH":      "CLAY_WEBHOOK_DACH",
}


async def run_monthly_batch() -> dict:
    """
    Selects the next batch of never-contacted companies from priority_tam,
    ordered by account_fit_score DESC then prioritized_at ASC, and inserts
    them into campaign_batches with an auto-incrementing batch_number.
    """
    sb = get_supabase()

    existing = fetch_all("campaign_batches", "domain, market, company_name, batch_number")
    contacted = {(r["domain"], r["market"], r["company_name"]) for r in existing}
    next_batch_number = max((r["batch_number"] for r in existing), default=0) + 1

    candidates = fetch_all(
        "priority_tam",
        "domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
        "esp_detected, esp_score, account_fit_score, account_narrative, "
        "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp",
        order_by=[("account_fit_score", True), ("prioritized_at", False)],
    )

    batch_month = date.today().replace(day=1).isoformat()

    uki_selected = [
        {**row, "batch_number": next_batch_number, "batch_month": batch_month}
        for row in candidates
        if row["market"] in UKI_MARKETS
        and (row["domain"], row["market"], row["company_name"]) not in contacted
    ][:UK_LIMIT]

    dach_selected = [
        {**row, "batch_number": next_batch_number, "batch_month": batch_month}
        for row in candidates
        if row["market"] in DACH_MARKETS
        and (row["domain"], row["market"], row["company_name"]) not in contacted
    ][:DACH_LIMIT]

    selected = uki_selected + dach_selected

    if not selected:
        logger.info("monthly_batch: no new candidates to select")
        return {
            "status": "ok", "selected": 0,
            "uki_selected": 0, "dach_selected": 0,
            "batch_number": next_batch_number, "batch_month": batch_month,
        }

    for i in range(0, len(selected), 100):
        sb.table("campaign_batches").insert(selected[i : i + 100]).execute()

    logger.info(
        "monthly_batch: inserted %d companies as batch #%d (%s) — UKI=%d DACH=%d",
        len(selected), next_batch_number, batch_month, len(uki_selected), len(dach_selected),
    )
    return {
        "status":        "ok",
        "selected":      len(selected),
        "uki_selected":  len(uki_selected),
        "dach_selected": len(dach_selected),
        "batch_number":  next_batch_number,
        "batch_month":   batch_month,
    }


async def push_batch_to_clay(batch_number: int) -> dict:
    """
    Reads unpushed campaign_batches for the given batch_number (clay_pushed_at IS NULL),
    POSTs each sequentially to the corresponding CLAY_WEBHOOK_{MARKET} env var URL,
    then stamps clay_pushed_at to prevent double-sends.
    """
    sb = get_supabase()

    rows = fetch_all(
        "campaign_batches",
        "id, domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
        "esp_detected, esp_score, account_fit_score, account_narrative, "
        "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "batch_number, batch_month",
        filters=[("eq", "batch_number", batch_number), ("is_", "clay_pushed_at", "null")],
    )

    if not rows:
        logger.info("monthly_batch: batch %d already fully pushed — nothing to send", batch_number)
        return {"status": "ok", "batch_number": batch_number, "webhooks": {}, "already_pushed": True}

    by_webhook: dict[str, list] = {}
    for row in rows:
        key = MARKET_TO_WEBHOOK_KEY.get(row["market"], f"CLAY_WEBHOOK_{row['market'].upper()}")
        by_webhook.setdefault(key, []).append(row)

    results = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def push_one(webhook_url: str, company: dict) -> None:
            for attempt in range(5):
                resp = await client.post(webhook_url, json=company)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 10 * (2 ** attempt)))
                    logger.warning("monthly_batch: 429 from Clay, waiting %ds (attempt %d)", wait, attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return
            raise RuntimeError("monthly_batch: Clay 429 — max retries exceeded")

        async def push_group(webhook_key: str, companies: list) -> None:
            webhook_url = os.environ.get(webhook_key)
            if not webhook_url:
                logger.warning("monthly_batch: %s not configured — skipping %d companies", webhook_key, len(companies))
                results[webhook_key] = {"status": "skipped", "reason": "no_webhook_configured", "companies": len(companies)}
                return
            pushed_at = datetime.now(timezone.utc).isoformat()
            pushed_ids = []
            for company in companies:
                row_id = company.pop("id")
                await push_one(webhook_url, company)
                pushed_ids.append(row_id)
            # Stamp clay_pushed_at in chunks to mark as sent
            for i in range(0, len(pushed_ids), 100):
                sb.table("campaign_batches").update({"clay_pushed_at": pushed_at}).in_("id", pushed_ids[i : i + 100]).execute()
            logger.info("monthly_batch: pushed %d companies via %s", len(companies), webhook_key)
            results[webhook_key] = {"status": "ok", "companies": len(companies)}

        await asyncio.gather(*[push_group(k, c) for k, c in by_webhook.items()])

    return {"status": "ok", "batch_number": batch_number, "webhooks": results}


async def _run_monthly_bg() -> None:
    try:
        batch_result = await run_monthly_batch()
        if batch_result["selected"] > 0:
            push_result = await push_batch_to_clay(batch_result["batch_number"])
        else:
            push_result = {"webhooks": {}}

        webhook_summary = " | ".join(
            f"{k.replace('CLAY_WEBHOOK_', '')}: {v.get('companies', 0)}"
            for k, v in push_result.get("webhooks", {}).items()
        ) or "none"

        await notify(
            f"✅ *Monthly batch complete*\n"
            f"• Batch #{batch_result['batch_number']} ({batch_result['batch_month']}) — {batch_result['selected']} companies\n"
            f"• UKI: {batch_result['uki_selected']} | DACH: {batch_result['dach_selected']}\n"
            f"• Pushed to Clay: {webhook_summary}"
        )
    except Exception as exc:
        await notify(f"❌ *Monthly batch failed* — `{exc}`", success=False)
        logger.exception("monthly_batch: background task failed")
        raise


@router.post("/pipelines/monthly-batch")
async def monthly_batch():
    """Selects next batch of uncontacted priority companies and logs them to campaign_batches."""
    return await run_monthly_batch()


@router.post("/pipelines/monthly-batch/push")
async def monthly_batch_push(batch_number: int):
    """Pushes a campaign batch to Clay webhooks, grouped by market."""
    try:
        return await push_batch_to_clay(batch_number)
    except Exception as exc:
        logger.exception("monthly_batch_push: failed for batch %d", batch_number)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pipelines/run-monthly")
async def run_monthly(background_tasks: BackgroundTasks):
    """1st-of-month cron: select batch + push to Clay. Runs in background to avoid timeout."""
    background_tasks.add_task(_run_monthly_bg)
    return {"status": "started"}
