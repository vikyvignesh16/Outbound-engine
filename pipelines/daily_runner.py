import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks

from pipelines.qualification import run_crm_check, run_qualification_rules, run_technographic
from pipelines.enrichment import submit_enrichment
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_daily_bg() -> None:
    try:
        crm    = await run_crm_check()
        rules  = await run_qualification_rules()
        tech   = await run_technographic()
        enrich = await submit_enrichment()
        await notify(
            f"✅ *Daily pipeline* — qualified {rules['qualified']} rows, "
            f"submitted {enrich['submitted']} to enrichment ({enrich['batches']} batches)"
        )
        logger.info("daily_runner: complete — qualified=%d submitted=%d", rules["qualified"], enrich["submitted"])
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        logger.exception("daily_runner: failed")


@router.post("/pipelines/run-daily")
async def run_daily(background_tasks: BackgroundTasks):
    """6am cron: qualify sourced_tam_v2 rows then submit enrichment batch. Runs in background."""
    background_tasks.add_task(_run_daily_bg)
    return {"status": "started"}
