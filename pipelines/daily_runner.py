import asyncio
import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all
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

        # Pipeline health snapshot
        sb = get_supabase()
        tam_rows = fetch_all("sourced_tam_v2", "market, crm_checked")
        priority_count = sb.table("priority_tam").select("id", count="exact").execute().count or 0

        market_stats: dict[str, dict] = {}
        for r in tam_rows:
            m = r["market"]
            if m not in market_stats:
                market_stats[m] = {"total": 0, "checked": 0}
            market_stats[m]["total"] += 1
            if r["crm_checked"]:
                market_stats[m]["checked"] += 1

        crm_lines = []
        for market, s in sorted(market_stats.items()):
            done = s["checked"] == s["total"]
            suffix = " ✅" if done else ""
            crm_lines.append(f"  ↳ {market}: {s['checked']:,} / {s['total']:,}{suffix}")

        tech_line   = "0 pending (all covered ✅)" if tech["processed"] == 0   else f"+{tech['processed']:,} processed"
        enrich_line = "0 pending (all covered ✅)" if enrich["submitted"] == 0  else f"{enrich['submitted']:,} submitted ({enrich['batches']} batches)"
        content_line = "0 contacts pending"        if content["submitted"] == 0 else f"{content['submitted']:,} submitted ({content['batches']} batches)"

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
            f"• CRM checked today: +{crm['processed']:,} companies\n"
            + "\n".join(crm_lines) + "\n"
            f"• Newly qualified: +{rules['newly_qualified']:,} companies\n"
            f"• Technographic: {tech_line}\n"
            f"• Enrichment: {enrich_line}\n"
            f"• Content: {content_line}\n"
            f"• Priority TAM: {priority_count:,} companies ready"
            f"{monthly_line}"
        )
        logger.info(
            "daily_runner: complete — crm=%d newly_qualified=%d enrich=%d content=%d",
            crm["processed"], rules["newly_qualified"], enrich["submitted"], content["submitted"],
        )
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        logger.exception("daily_runner: failed")


@router.post("/pipelines/run-daily")
async def run_daily(background_tasks: BackgroundTasks):
    """6am cron: qualify sourced_tam_v2 rows then submit enrichment batch. Runs in background."""
    background_tasks.add_task(_run_daily_bg)
    return {"status": "started"}
