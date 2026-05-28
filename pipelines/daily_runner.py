import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks

from pipelines.qualification import run_crm_check, run_qualification_rules, run_technographic
from pipelines.enrichment import submit_enrichment
from pipelines.content import submit_content
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_daily_bg() -> None:
    try:
        crm     = await run_crm_check()
        rules   = await run_qualification_rules()
        tech    = await run_technographic()
        enrich  = await submit_enrichment()
        content = await submit_content()
        await notify(
            f"✅ *Daily pipeline complete*\n"
            f"• CRM checked: {crm['processed']} companies\n"
            f"• Qualified: {rules['qualified']} companies\n"
            f"• Technographic: {tech['processed']} companies\n"
            f"• Submitted to enrichment: {enrich['submitted']} ({enrich['batches']} batches)\n"
            f"• Submitted to content: {content['submitted']} contacts ({content['batches']} batches)"
        )
        logger.info(
            "daily_runner: complete — crm=%d qualified=%d enrich=%d content=%d",
            crm["processed"], rules["qualified"], enrich["submitted"], content["submitted"],
        )
    except NotImplementedError:
        # Content prompt not yet defined — skip without failing the daily run
        await notify(
            f"✅ *Daily pipeline complete* (content pending prompt)\n"
            f"• CRM checked: {crm['processed']} companies\n"
            f"• Qualified: {rules['qualified']} companies\n"
            f"• Technographic: {tech['processed']} companies\n"
            f"• Submitted to enrichment: {enrich['submitted']} ({enrich['batches']} batches)"
        )
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        logger.exception("daily_runner: failed")


@router.post("/pipelines/run-daily")
async def run_daily(background_tasks: BackgroundTasks):
    """6am cron: qualify sourced_tam_v2 rows then submit enrichment batch. Runs in background."""
    background_tasks.add_task(_run_daily_bg)
    return {"status": "started"}
