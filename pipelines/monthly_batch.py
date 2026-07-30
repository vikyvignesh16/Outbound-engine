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

MARKET_GROUPS: dict[str, set[str]] = {
    "UKI":  {"UK", "Ireland"},
    "DACH": {"DE", "AT", "CH"},
    "US":   {"US"},
    "FR":   {"FR"},
}
MARKET_TO_GROUP: dict[str, str] = {m: g for g, ms in MARKET_GROUPS.items() for m in ms}
GROUP_LIMITS: dict[str, int] = {
    "UKI":  500,
    "DACH": 500,
    "US":   500,
    "FR":   500,
}

MARKET_TO_WEBHOOK_KEY: dict[str, str] = {
    "UK":      "CLAY_WEBHOOK_UK",
    "Ireland": "CLAY_WEBHOOK_UK",
    "DE":      "CLAY_WEBHOOK_DACH",
    "AT":      "CLAY_WEBHOOK_DACH",
    "CH":      "CLAY_WEBHOOK_DACH",
}


async def run_monthly_batch(groups: list[str] | None = None) -> dict:
    """
    Selects the next batch of never-contacted companies from priority_tam,
    ordered by account_fit_score DESC then prioritized_at ASC, and inserts
    them into campaign_batches.

    batch_number is scoped PER MARKET GROUP, not global — each of UKI, DACH,
    US, FR has its own independent 1, 2, 3... sequence, since they're pushed
    to Clay separately and "batch #N" should mean something on its own within
    a group rather than being a shared counter that happens to land two
    unrelated groups on the same number.

    `groups` restricts selection to a subset of MARKET_GROUPS (e.g. ["DACH", "US"])
    for a one-off run covering only those markets — defaults to all groups (the
    1st-of-month cron behavior). The idempotency guard below is scoped to the
    active markets only, so running one group doesn't get silently skipped by
    another group's batch already existing this month.
    """
    sb = get_supabase()

    active_groups = groups or list(MARKET_GROUPS.keys())
    active_markets = {m for g in active_groups for m in MARKET_GROUPS[g]}

    batch_month = date.today().replace(day=1).isoformat()

    existing = fetch_all("campaign_batches", "domain, market, company_name, batch_number, batch_month")

    # Idempotency guard — if a batch already exists this month for one of the
    # ACTIVE markets, return it. Scoped to active_markets so e.g. a UK batch
    # already existing this month doesn't block a DACH/US-only run.
    this_month = [r for r in existing if r.get("batch_month") == batch_month and r["market"] in active_markets]
    if this_month:
        existing_batch_numbers = {
            MARKET_TO_GROUP[r["market"]]: r["batch_number"] for r in this_month
        }
        logger.info("monthly_batch: batch already exists for %s (%s) — skipping: %s",
                    batch_month, active_groups, existing_batch_numbers)
        return {
            "status": "already_exists",
            "selected": len(this_month),
            "batch_numbers": existing_batch_numbers,
            "batch_month": batch_month,
        }

    contacted = {(r["domain"], r["market"], r["company_name"]) for r in existing}

    # Next batch_number computed independently per group — DACH's first batch
    # is 1 regardless of how many batches UKI or US have already run.
    next_batch_number_by_group = {
        g: max(
            (r["batch_number"] for r in existing if r["market"] in MARKET_GROUPS[g]),
            default=0,
        ) + 1
        for g in active_groups
    }

    candidates = fetch_all(
        "priority_tam",
        "domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
        "esp_detected, esp_score, account_fit_score, account_narrative, "
        "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "business_model, company_revenue, multi_entity, tam_segment, "
        "icp_archetype_primary, icp_archetype_secondary, icp_archetype_evidence, "
        "tech_score, tech_stack_primary, tech_category, tech_esp, tech_crm, "
        "tech_cms, tech_ecommerce, tech_analytics, tech_cdn, tech_payment, "
        "tech_marketing, tech_chat, tech_hosting, tech_ab_testing, tech_tag_manager",
        order_by=[("account_fit_score", True), ("prioritized_at", False)],
    )

    selected_by_group: dict[str, list] = {}
    for g in active_groups:
        markets = MARKET_GROUPS[g]
        limit = GROUP_LIMITS[g]
        batch_number = next_batch_number_by_group[g]
        selected_by_group[g] = [
            {**row, "batch_number": batch_number, "batch_month": batch_month}
            for row in candidates
            if row["market"] in markets
            and (row["domain"], row["market"], row["company_name"]) not in contacted
        ][:limit]

    selected = [row for rows in selected_by_group.values() for row in rows]
    group_counts = {g: len(rows) for g, rows in selected_by_group.items()}

    if not selected:
        logger.info("monthly_batch: no new candidates to select for %s", active_groups)
        return {
            "status": "ok", "selected": 0,
            "group_counts": {g: 0 for g in active_groups},
            "batch_numbers": next_batch_number_by_group, "batch_month": batch_month,
        }

    for i in range(0, len(selected), 100):
        sb.table("campaign_batches").insert(selected[i : i + 100]).execute()

    logger.info(
        "monthly_batch: inserted %d companies (%s) as batches %s",
        len(selected), batch_month, next_batch_number_by_group,
    )
    return {
        "status":        "ok",
        "selected":      len(selected),
        "group_counts":  group_counts,
        "batch_numbers": next_batch_number_by_group,
        "batch_month":   batch_month,
    }


async def push_batch_to_clay(market_group: str, batch_number: int) -> dict:
    """
    Reads unpushed campaign_batches for the given (market_group, batch_number)
    (clay_pushed_at IS NULL), POSTs each sequentially to the corresponding
    CLAY_WEBHOOK_{MARKET} env var URL, then stamps clay_pushed_at to prevent
    double-sends.

    batch_number alone no longer identifies a batch uniquely — DACH's batch 1
    and US's batch 1 are different cohorts — so market_group narrows the
    campaign_batches filter to just that group's markets.
    """
    sb = get_supabase()

    rows = fetch_all(
        "campaign_batches",
        "id, domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date, "
        "esp_detected, esp_score, account_fit_score, account_narrative, "
        "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "business_model, company_revenue, multi_entity, tam_segment, "
        "icp_archetype_primary, icp_archetype_secondary, icp_archetype_evidence, "
        "tech_score, tech_stack_primary, tech_category, tech_esp, tech_crm, "
        "tech_cms, tech_ecommerce, tech_analytics, tech_cdn, tech_payment, "
        "tech_marketing, tech_chat, tech_hosting, tech_ab_testing, tech_tag_manager, "
        "batch_number, batch_month",
        filters=[("eq", "batch_number", batch_number), ("is_", "clay_pushed_at", "null")],
    )
    rows = [r for r in rows if r["market"] in MARKET_GROUPS[market_group]]

    if not rows:
        logger.info("monthly_batch: %s batch %d already fully pushed — nothing to send", market_group, batch_number)
        return {"status": "ok", "market_group": market_group, "batch_number": batch_number, "webhooks": {}, "already_pushed": True}

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

    return {"status": "ok", "market_group": market_group, "batch_number": batch_number, "webhooks": results}


async def _run_monthly_bg(groups: list[str] | None = None) -> None:
    try:
        batch_result = await run_monthly_batch(groups=groups)
        batch_numbers = batch_result.get("batch_numbers", {})
        group_counts = batch_result.get("group_counts", {})

        push_results: dict[str, dict] = {}
        for g, count in group_counts.items():
            if count > 0:
                push_results[g] = await push_batch_to_clay(g, batch_numbers[g])

        webhook_summary = " | ".join(
            f"{k.replace('CLAY_WEBHOOK_', '')}: {v.get('companies', 0)}"
            for push_result in push_results.values()
            for k, v in push_result.get("webhooks", {}).items()
        ) or "none"

        group_summary = " | ".join(
            f"{g} batch #{batch_numbers.get(g)}: {c}" for g, c in group_counts.items()
        ) or "none"

        await notify(
            f"✅ *Monthly batch complete*\n"
            f"• {batch_result['batch_month']} — {batch_result['selected']} companies\n"
            f"• {group_summary}\n"
            f"• Pushed to Clay: {webhook_summary}"
        )
    except Exception as exc:
        await notify(f"❌ *Monthly batch failed* — `{exc}`", success=False)
        logger.exception("monthly_batch: background task failed")
        raise


@router.post("/pipelines/monthly-batch")
async def monthly_batch(groups: str | None = None):
    """Selects next batch of uncontacted priority companies and logs them to campaign_batches.
    Pass ?groups=DACH,US to restrict selection to a subset of MARKET_GROUPS (defaults to all)."""
    group_list = groups.split(",") if groups else None
    return await run_monthly_batch(groups=group_list)


@router.post("/pipelines/monthly-batch/push")
async def monthly_batch_push(market_group: str, batch_number: int):
    """Pushes a campaign batch to Clay webhooks. market_group + batch_number together
    identify the batch, since batch_number alone is scoped per group (not global)."""
    try:
        return await push_batch_to_clay(market_group, batch_number)
    except Exception as exc:
        logger.exception("monthly_batch_push: failed for %s batch %d", market_group, batch_number)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pipelines/run-monthly")
async def run_monthly(background_tasks: BackgroundTasks):
    """1st-of-month cron: select batch + push to Clay. Runs in background to avoid timeout."""
    background_tasks.add_task(_run_monthly_bg)
    return {"status": "started"}
