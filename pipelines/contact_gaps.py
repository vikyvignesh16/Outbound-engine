import logging
import os
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all
from utils.phantombuster import (
    launch_agent, get_container, is_finished, is_error, get_result_rows,
)
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Sales Navigator URL builder ────────────────────────────────────────────────

_REGION: dict[str, tuple[str, str]] = {
    "UK": ("101165590", "United Kingdom"),
    "IE": ("104738515", "Ireland"),
    "DE": ("101282230", "Germany"),
    "AT": ("103883259", "Austria"),
    "CH": ("106693272", "Switzerland"),
}

_TITLE_FILTER = (
    "(type:CURRENT_TITLE,values:List("
    "(text:Lifecycle,selectionType:INCLUDED),"
    "(text:CRM,selectionType:INCLUDED),"
    "(text:Marketing Automation,selectionType:INCLUDED),"
    "(text:Marketing Communications,selectionType:INCLUDED),"
    "(text:CMO,selectionType:INCLUDED),"
    "(id:716,text:Chief Marketing Officer,selectionType:INCLUDED)"
    "))"
)


def _build_sales_nav_url(company_org_id: str, company_name: str, market: str) -> str:
    region_id, region_text = _REGION.get(market, ("101165590", "United Kingdom"))
    region_filter = (
        f"(type:REGION,values:List("
        f"(id:{region_id},text:{region_text},selectionType:INCLUDED)"
        f"))"
    )
    company_filter = (
        f"(type:CURRENT_COMPANY,values:List("
        f"(id:urn:li:organization:{company_org_id},"
        f"text:{company_name},"
        f"selectionType:INCLUDED,parent:(id:0))"
        f"))"
    )
    query = f"(filters:List({_TITLE_FILTER},{region_filter},{company_filter}))"
    return f"https://www.linkedin.com/sales/search/people?query={quote(query)}"


# ── Gap detection ──────────────────────────────────────────────────────────────

def detect_gaps(batch_number: int) -> int:
    """Find domains in batch with 0 sourced contacts. Writes pending rows to contact_gaps."""
    batch_rows = fetch_all(
        "campaign_batches", "domain,company_name,market",
        filters=[("eq", "batch_number", batch_number)],
    )
    contacted = {
        r["domain"]
        for r in fetch_all(
            "sourced_contacts", "domain",
            filters=[("eq", "batch_number", batch_number)],
        )
    }
    gaps = [r for r in batch_rows if r["domain"] not in contacted]
    if not gaps:
        return 0

    sb = get_supabase()
    for gap in gaps:
        sb.table("contact_gaps").upsert({
            "domain":               gap["domain"],
            "company_name":         gap.get("company_name"),
            "market":               gap.get("market"),
            "batch_number":         batch_number,
            "gap_reason":           "no_contacts",
            "phantombuster_status": "pending",
        }, on_conflict="domain,batch_number").execute()

    logger.info("contact_gaps: detected %d gaps for batch %d", len(gaps), batch_number)
    return len(gaps)


# ── Phase 1 — LinkedIn Company Data Extractor ──────────────────────────────────

def run_phase1(batch_number: int) -> int:
    """Launch LinkedIn Company Data Extractor for each pending gap."""
    pending = fetch_all(
        "contact_gaps", "id,domain,company_name,market",
        filters=[
            ("eq", "phantombuster_status", "pending"),
            ("eq", "batch_number", batch_number),
        ],
    )
    if not pending:
        return 0

    sb = get_supabase()
    agent_id = os.environ["PHANTOMBUSTER_COMPANY_EXTRACTOR_ID"]
    launched = 0

    for row in pending:
        tam = fetch_all(
            "sourced_tam_v2", "linkedin_url",
            filters=[("eq", "domain", row["domain"])],
            limit=1,
        )
        if not tam or not tam[0].get("linkedin_url"):
            sb.table("contact_gaps").update({
                "phantombuster_status": "failed",
                "gap_reason": "no_linkedin_url",
            }).eq("id", row["id"]).execute()
            logger.warning("contact_gaps: no linkedin_url for %s", row["domain"])
            continue

        try:
            container_id = launch_agent(agent_id, {"linkedInCompanyUrl": tam[0]["linkedin_url"]})
            sb.table("contact_gaps").update({
                "phantombuster_status": "extracting_company",
                "phantom_id": container_id,
                "phase": 1,
            }).eq("id", row["id"]).execute()
            launched += 1
            logger.info("contact_gaps: phase1 launched for %s → container %s", row["domain"], container_id)
        except Exception as exc:
            logger.error("contact_gaps: phase1 launch failed for %s: %s", row["domain"], exc)
            sb.table("contact_gaps").update({"phantombuster_status": "failed"}).eq("id", row["id"]).execute()

    return launched


def poll_phase1() -> int:
    """Check running Phase 1 containers. Advance completed rows to building_url."""
    rows = fetch_all(
        "contact_gaps", "id,domain,company_name,market,batch_number,phantom_id",
        filters=[("eq", "phantombuster_status", "extracting_company")],
    )
    if not rows:
        return 0

    sb = get_supabase()
    advanced = 0

    for row in rows:
        try:
            container = get_container(row["phantom_id"])
            if not is_finished(container):
                continue
            if is_error(container):
                sb.table("contact_gaps").update({"phantombuster_status": "failed"}).eq("id", row["id"]).execute()
                continue

            results = get_result_rows(container)
            if not results:
                sb.table("contact_gaps").update({
                    "phantombuster_status": "failed",
                    "gap_reason": "no_company_id_returned",
                }).eq("id", row["id"]).execute()
                continue

            company_data = results[0]
            # Field name TBC from first real run — try common variants
            org_id = (
                company_data.get("linkedInId") or
                company_data.get("companyId") or
                company_data.get("id") or
                company_data.get("linkedinId")
            )
            if not org_id:
                logger.warning(
                    "contact_gaps: org_id field unknown for %s — keys: %s",
                    row["domain"], list(company_data.keys()),
                )
                sb.table("contact_gaps").update({
                    "phantombuster_status": "failed",
                    "gap_reason": "org_id_field_unknown",
                }).eq("id", row["id"]).execute()
                continue

            sales_nav_url = _build_sales_nav_url(str(org_id), row["company_name"] or "", row["market"] or "UK")
            sb.table("contact_gaps").update({
                "linkedin_company_id": str(org_id),
                "sales_nav_url":       sales_nav_url,
                "phantombuster_status": "building_url",
            }).eq("id", row["id"]).execute()
            advanced += 1
            logger.info("contact_gaps: phase1 complete for %s → org_id %s", row["domain"], org_id)
        except Exception as exc:
            logger.error("contact_gaps: poll_phase1 error for %s: %s", row["domain"], exc)

    return advanced


# ── Phase 2 — Sales Navigator Search Export ────────────────────────────────────

def run_phase2() -> int:
    """Launch Sales Navigator Search Export for each row that has a sales_nav_url."""
    rows = fetch_all(
        "contact_gaps", "id,domain,sales_nav_url",
        filters=[("eq", "phantombuster_status", "building_url")],
    )
    if not rows:
        return 0

    sb = get_supabase()
    agent_id = os.environ["PHANTOMBUSTER_SALES_NAV_ID"]
    launched = 0

    for row in rows:
        if not row.get("sales_nav_url"):
            continue
        try:
            container_id = launch_agent(agent_id, {
                "salesNavigatorUrl": row["sales_nav_url"],
                "numberOfProfiles": 25,
            })
            sb.table("contact_gaps").update({
                "phantombuster_status": "scraping_contacts",
                "phantom_id": container_id,
                "phase": 2,
            }).eq("id", row["id"]).execute()
            launched += 1
            logger.info("contact_gaps: phase2 launched for %s → container %s", row["domain"], container_id)
        except Exception as exc:
            logger.error("contact_gaps: phase2 launch failed for %s: %s", row["domain"], exc)
            sb.table("contact_gaps").update({"phantombuster_status": "failed"}).eq("id", row["id"]).execute()

    return launched


def poll_phase2() -> int:
    """Check running Phase 2 containers. Write contacts to sourced_contacts when done."""
    rows = fetch_all(
        "contact_gaps", "id,domain,company_name,market,batch_number,phantom_id",
        filters=[("eq", "phantombuster_status", "scraping_contacts")],
    )
    if not rows:
        return 0

    sb = get_supabase()
    completed = 0

    for row in rows:
        try:
            container = get_container(row["phantom_id"])
            if not is_finished(container):
                continue
            if is_error(container):
                sb.table("contact_gaps").update({"phantombuster_status": "failed"}).eq("id", row["id"]).execute()
                continue

            result_rows = get_result_rows(container)
            contacts = [_map_contact(r, row) for r in result_rows if r]
            # Require at least a LinkedIn URL to be usable
            contacts = [c for c in contacts if c.get("linkedin_url")]

            for contact in contacts:
                sb.table("sourced_contacts").upsert(contact, on_conflict="domain,email").execute()

            now_iso = datetime.now(timezone.utc).isoformat()
            sb.table("contact_gaps").update({
                "phantombuster_status": "completed",
                "contacts_found":       len(contacts),
                "completed_at":         now_iso,
            }).eq("id", row["id"]).execute()
            completed += 1
            logger.info("contact_gaps: phase2 complete for %s → %d contacts", row["domain"], len(contacts))
        except Exception as exc:
            logger.error("contact_gaps: poll_phase2 error for %s: %s", row["domain"], exc)

    return completed


def _map_contact(pb_row: dict, gap_row: dict) -> dict:
    return {
        "domain":       gap_row["domain"],
        "company_name": gap_row.get("company_name"),
        "market":       gap_row.get("market"),
        "batch_number": gap_row.get("batch_number"),
        "email":        pb_row.get("email"),
        "first_name":   pb_row.get("firstName") or pb_row.get("first_name"),
        "last_name":    pb_row.get("lastName") or pb_row.get("last_name"),
        "job_title":    pb_row.get("title") or pb_row.get("occupation"),
        "seniority":    pb_row.get("seniority"),
        "linkedin_url": pb_row.get("profileUrl") or pb_row.get("linkedInUrl") or pb_row.get("linkedin_url"),
        "raw":          pb_row,
    }


# ── FastAPI endpoints ──────────────────────────────────────────────────────────

async def _run_contact_gaps_bg(batch_number: int) -> None:
    try:
        gaps    = detect_gaps(batch_number)
        launched = run_phase1(batch_number)
        await notify(
            f"🔍 *Contact gaps — batch #{batch_number}*\n"
            f"• Gaps detected: {gaps}\n"
            f"• Phase 1 jobs launched: {launched}",
        )
    except Exception as exc:
        await notify(f"❌ *Contact gaps failed (batch #{batch_number})* — `{exc}`", success=False)
        logger.exception("contact_gaps: background task failed")


@router.post("/pipelines/contact-gaps")
async def run_contact_gaps(batch_number: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_contact_gaps_bg, batch_number)
    return {"status": "started", "batch_number": batch_number}


@router.post("/pipelines/contact-gaps/poll")
async def poll_contact_gaps():
    """Advance all in-flight PhantomBuster jobs. Run every 30 min via Railway cron."""
    p1 = poll_phase1()
    launched = run_phase2()   # rows that just finished phase 1 → launch phase 2
    p2 = poll_phase2()
    logger.info("contact_gaps/poll: p1_advanced=%d p2_launched=%d p2_completed=%d", p1, launched, p2)
    return {"phase1_advanced": p1, "phase2_launched": launched, "phase2_completed": p2}
