import asyncio
import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all
from pipelines.qualification import run_crm_check, run_qualification_rules, run_technographic
from pipelines.enrichment import submit_enrichment, run_prioritize
from pipelines.content import submit_content, CONTENT_GENERATION_MARKETS
from pipelines.monthly_batch import run_monthly_batch, push_batch_to_clay
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_daily_bg() -> None:
    try:
        crm     = await run_crm_check()
        rules   = await run_qualification_rules()
        tech    = await run_technographic()

        # If technographic was skipped (another call already holds the lock —
        # e.g. a large manual backlog run in progress), do NOT proceed to
        # enrichment/prioritize this cycle. Rows should only get scored and
        # promoted once technographic has actually had a chance to complete for
        # them, per an explicit decision to sequence it that way — the lock only
        # ever protected the API calls from colliding, not this ordering.
        if tech.get("status") == "skipped":
            logger.info("daily_runner: technographic skipped (%s) — deferring enrichment/prioritize to next cycle", tech.get("reason"))
            enrich = {"status": "deferred", "submitted": 0, "batches": 0, "batch_ids": []}
            content = {"status": "deferred", "submitted": 0, "batches": 0, "batch_ids": []}
            prioritize = {"status": "deferred", "prioritized": 0, "skipped_by_gate": 0}
        else:
            enrich = await submit_enrichment()
            # Scoped inside submit_content() itself via CONTENT_GENERATION_MARKETS
            # (currently DACH + US only) — other markets' pending contacts are
            # left untouched (content_generated_at stays NULL) rather than
            # gated behind a separate all-or-nothing flag here.
            content = await submit_content()
            prioritize = await run_prioritize()

        # Pipeline health snapshot
        sb = get_supabase()
        tam_rows        = fetch_all("sourced_tam_v2", "market, crm_checked")
        sourced_total   = sb.table("sourced_tam_v2").select("id", count="exact").execute().count or 0
        qualified_total = sb.table("qualified_tam_v2").select("id", count="exact").execute().count or 0
        tech_done       = (
            sb.table("qualified_tam_v2").select("id", count="exact")
            .not_.is_("esp_score", "null").execute().count or 0
        )
        enriched_done   = (
            sb.table("qualified_tam_v2").select("id", count="exact")
            .not_.is_("account_fit_score", "null").execute().count or 0
        )
        priority_count  = sb.table("priority_tam").select("id", count="exact").execute().count or 0

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
        markets_line = "/".join(sorted(CONTENT_GENERATION_MARKETS))
        if content["submitted"] == 0:
            content_line = f"0 contacts pending ({markets_line} only)"
        else:
            content_line = f"{content['submitted']:,} submitted ({content['batches']} batches, {markets_line} only)"

        monthly_line = ""
        if date.today().day == 1:
            batch_result = await run_monthly_batch()
            batch_numbers = batch_result.get("batch_numbers", {})
            group_counts = batch_result.get("group_counts", {})

            group_lines = []
            for group, count in group_counts.items():
                if count <= 0:
                    continue
                push_result = await push_batch_to_clay(group, batch_numbers[group])
                summary = " | ".join(
                    f"{k.replace('CLAY_WEBHOOK_', '')}: {v.get('companies', 0)}"
                    for k, v in push_result.get("webhooks", {}).items()
                ) or "none"
                group_lines.append(f"{group} batch #{batch_numbers[group]}: {count} companies — {summary}")

            monthly_line = ("\n• " + "\n• ".join(group_lines)) if group_lines else "\n• Monthly batch: 0 companies"
            logger.info(
                "daily_runner: monthly batch — %d selected across %s",
                batch_result["selected"], batch_numbers,
            )

        await notify(
            f"✅ *Daily pipeline complete*\n"
            f"• CRM checked today: +{crm['processed']:,} companies\n"
            + "\n".join(crm_lines) + "\n"
            f"• Newly qualified: +{rules['newly_qualified']:,} companies\n"
            f"• Technographic: {tech_line}\n"
            f"• Enrichment: {enrich_line}\n"
            f"• Content: {content_line}\n"
            f"• Priority TAM refreshed: {prioritize['prioritized']:,} companies\n"
            f"\n*Pipeline health (qualified_tam_v2 → priority_tam):*\n"
            f"  Step 1 — Qualified: {qualified_total:,} / {sourced_total:,}\n"
            f"  Step 2 — Technographic: {tech_done:,} / {qualified_total:,}\n"
            f"  Step 3 — AI enriched: {enriched_done:,} / {qualified_total:,}\n"
            f"  Priority TAM (score ≥ 3): {priority_count:,} ready"
            f"{monthly_line}"
        )
        logger.info(
            "daily_runner: complete — crm=%d newly_qualified=%d enrich=%d content=%d prioritized=%d",
            crm["processed"], rules["newly_qualified"], enrich["submitted"], content["submitted"], prioritize["prioritized"],
        )
    except Exception as exc:
        await notify(f"❌ *Daily pipeline failed* — `{exc}`", success=False)
        logger.exception("daily_runner: failed")


@router.post("/pipelines/run-daily")
async def run_daily(background_tasks: BackgroundTasks):
    """6am cron: qualify sourced_tam_v2 rows then submit enrichment batch. Runs in background."""
    background_tasks.add_task(_run_daily_bg)
    return {"status": "started"}
