import logging
from datetime import date

from fastapi import APIRouter

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

BATCH_LIMIT = 1000


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


@router.post("/pipelines/monthly-batch")
async def monthly_batch():
    """Selects next 1000 uncontacted priority companies and logs them to campaign_batches."""
    return await run_monthly_batch()
