from fastapi import APIRouter

from pipelines.qualification import run_crm_check, run_qualification_rules, run_technographic
from pipelines.enrichment import submit_enrichment
from utils.slack import notify

router = APIRouter()


@router.post("/pipelines/run-daily")
async def run_daily():
    """6am cron: qualify new sourced_tam_v2 rows then submit enrichment batch."""
    try:
        crm   = await run_crm_check()
        rules = await run_qualification_rules()
        tech  = await run_technographic()
        enrich = await submit_enrichment()
        await notify(
            f"✅ *Daily pipeline* — qualified {rules['qualified']} rows, "
            f"submitted {enrich['submitted']} to enrichment ({enrich['batches']} batches)"
        )
        return {
            "qualify": {"crm": crm, "rules": rules, "technographic": tech},
            "enrich":  enrich,
        }
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        raise
