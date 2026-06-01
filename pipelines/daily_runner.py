import asyncio
import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks

from pipelines.qualification import run_crm_check, run_qualification_rules, run_technographic
from pipelines.enrichment import submit_enrichment
from pipelines.content import submit_content
from pipelines.monthly_batch import run_monthly_batch, push_batch_to_clay
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

        monthly_line = ""
        if date.today().day == 1:
            batch_result = await run_monthly_batch()
            if batch_result["selected"] > 0:
                push_result = await push_batch_to_clay(batch_result["batch_number"])
            else:
                push_result = {"webhooks": {}}
            webhook_summary = " | ".join(
                f"{k.replace('CLAY_WEBHOOK_', '')}: {v.get('companies', 0)}"
                for k, v in push_result.get("webhooks", {}).items()
            ) or "none"
            monthly_line = (
                f"\n• Monthly batch #{batch_result['batch_number']}: "
                f"{batch_result['selected']} companies — {webhook_summary}"
            )
            logger.info(
                "daily_runner: monthly batch #%d — %d selected",
                batch_result["batch_number"], batch_result["selected"],
            )

        await notify(
            f"✅ *Daily pipeline complete*\n"
            f"• CRM checked: {crm['processed']} companies\n"
            f"• Qualified: {rules['qualified']} companies\n"
            f"• Technographic: {tech['processed']} companies\n"
            f"• Submitted to enrichment: {enrich['submitted']} ({enrich['batches']} batches)\n"
            f"• Submitted to content: {content['submitted']} contacts ({content['batches']} batches)"
            f"{monthly_line}"
        )
        logger.info(
            "daily_runner: complete — crm=%d qualified=%d enrich=%d content=%d",
            crm["processed"], rules["qualified"], enrich["submitted"], content["submitted"],
        )
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        logger.exception("daily_runner: failed")


@router.post("/pipelines/run-daily")
async def run_daily(background_tasks: BackgroundTasks):
    """6am cron: qualify sourced_tam_v2 rows then submit enrichment batch. Runs in background."""
    background_tasks.add_task(_run_daily_bg)
    return {"status": "started"}
