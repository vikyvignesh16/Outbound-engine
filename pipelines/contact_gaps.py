import logging
import os
import re
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
    "(id:716,text:Chief Marketing Officer,selectionType:INCLUDED),"
    "(text:marketing,selectionType:INCLUDED),"
    "(text:communications,selectionType:INCLUDED)"
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


def _csv_name(company_name: str | None) -> str:
    """Filesystem-safe name for PB output CSV: sanitized company name + unix timestamp.
    Unique per launch even when a company is re-scraped later."""
    import time as _time
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (company_name or "")).strip("_") or "company"
    return f"{slug}_{int(_time.time())}"


# ── Subsidiary detection ───────────────────────────────────────────────────────

def _is_subsidiary(linkedin_url: str, domain: str) -> bool:
    """True if another domain shares this LinkedIn URL (acquired / subsidiary company)."""
    matches = fetch_all(
        "sourced_tam_v2", "domain",
        filters=[("eq", "linkedin_url", linkedin_url), ("neq", "domain", domain)],
        limit=1,
    )
    return len(matches) > 0


# ── Campaign batch count update ────────────────────────────────────────────────

def _update_campaign_counts(domain: str, batch_number: int, count: int, source: str) -> None:
    get_supabase().table("campaign_batches").update({
        "contacts_sourced_count":  count,
        "contacts_sourced_source": source if count > 0 else "none",
    }).eq("domain", domain).eq("batch_number", batch_number).execute()


# ── Gap detection ──────────────────────────────────────────────────────────────

def detect_gaps(batch_number: int) -> int:
    """Find domains in batch with no contacts yet (across both sourced_contacts
    and phantombuster_contacts) and insert pending rows in contact_gaps.

    Idempotent: companies that already have a row in contact_gaps for this batch
    are left untouched, regardless of their current phantombuster_status.  This
    is important because the day-2 monthly cron may fire multiple times when
    re-deploys happen, and we never want to reset terminal rows back to pending
    (would cause PB to re-scrape and burn credits)."""
    batch_rows = fetch_all(
        "campaign_batches", "domain,company_name,market",
        filters=[("eq", "batch_number", batch_number)],
    )
    contacted = {
        r["domain"]
        for r in fetch_all("sourced_contacts", "domain",
                           filters=[("eq", "batch_number", batch_number)])
    }
    pb_seen = {
        r["domain"]
        for r in fetch_all("phantombuster_contacts", "domain",
                           filters=[("eq", "batch_number", batch_number)])
    }
    already_tracked = {
        r["domain"]
        for r in fetch_all("contact_gaps", "domain",
                           filters=[("eq", "batch_number", batch_number)])
    }
    gaps = [
        r for r in batch_rows
        if r["domain"] not in contacted
        and r["domain"] not in pb_seen
        and r["domain"] not in already_tracked
    ]
    if not gaps:
        return 0

    sb = get_supabase()
    # Insert (not upsert) — `already_tracked` guards us against conflicts so the
    # phantombuster_status of existing rows is never overwritten.
    for i in range(0, len(gaps), 100):
        chunk = [{
            "domain":               g["domain"],
            "company_name":         g.get("company_name"),
            "market":               g.get("market"),
            "batch_number":         batch_number,
            "gap_reason":           "no_contacts",
            "phantombuster_status": "pending",
        } for g in gaps[i:i+100]]
        sb.table("contact_gaps").insert(chunk).execute()

    logger.info("contact_gaps: detected %d new gaps for batch %d", len(gaps), batch_number)
    return len(gaps)


# ── Phase 1 — LinkedIn Company Data Extractor ──────────────────────────────────

DAILY_PHASE1_LIMIT = 150     # PhantomBuster's LinkedIn Company Extractor limit/day
PHASE2_BATCH_SIZE  = 5       # Sales Nav URLs per Phase 2 launch (5x throughput)
PUBLIC_API_BASE    = "https://brevooutboundengine-production.up.railway.app"


def run_phase1(batch_number: int) -> int:
    """Launch LinkedIn Company Data Extractor for ONE pending gap, if no PB container
    is currently in flight AND today's launch count is below DAILY_PHASE1_LIMIT.

    PhantomBuster workspaces have a single parallel-execution slot AND a daily
    cap of 150 LinkedIn Company Extractor runs.  We enforce both."""
    in_flight = fetch_all(
        "contact_gaps", "id",
        filters=[("in_", "phantombuster_status", ["extracting_company", "scraping_contacts"])],
        limit=1,
    )
    if in_flight:
        logger.info("contact_gaps: phase1 skipped — another container in flight")
        return 0

    today_utc_midnight = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
    today_launches = fetch_all(
        "contact_gaps", "id",
        filters=[("gte", "phase1_launched_at", today_utc_midnight)],
    )
    if len(today_launches) >= DAILY_PHASE1_LIMIT:
        logger.info(
            "contact_gaps: phase1 skipped — daily cap reached (%d/%d launches today)",
            len(today_launches), DAILY_PHASE1_LIMIT,
        )
        return 0

    pending = fetch_all(
        "contact_gaps", "id,domain,company_name,market",
        filters=[
            ("eq", "phantombuster_status", "pending"),
            ("eq", "batch_number", batch_number),
        ],
        limit=1,
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

        linkedin_url = tam[0]["linkedin_url"]

        # Skip subsidiaries — same LinkedIn URL as another company
        if _is_subsidiary(linkedin_url, row["domain"]):
            sb.table("contact_gaps").update({
                "phantombuster_status": "subsidiary_skipped",
            }).eq("id", row["id"]).execute()
            _update_campaign_counts(row["domain"], batch_number, 0, "subsidiary")
            logger.info("contact_gaps: subsidiary_skipped for %s", row["domain"])
            continue

        try:
            # spreadsheetUrl = the LinkedIn company page URL (confirmed from PB agent config)
            container_id = launch_agent(agent_id, {"spreadsheetUrl": linkedin_url})
            sb.table("contact_gaps").update({
                "phantombuster_status": "extracting_company",
                "phantom_id": container_id,
                "phase": 1,
                "phase1_launched_at": datetime.now(timezone.utc).isoformat(),
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
            # PB Company Extractor result fields (confirmed from a successful scrape):
            #   linkedinID  → the canonical LinkedIn organisation id used by Sales Nav
            #   mainCompanyID → same value, surfaced when the URL hits a redirected page
            org_id = (
                company_data.get("linkedinID") or
                company_data.get("mainCompanyID") or
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

            sales_nav_url = _build_sales_nav_url(
                str(org_id), row["company_name"] or "", row["market"] or "UK"
            )
            sb.table("contact_gaps").update({
                "linkedin_company_id":  str(org_id),
                "sales_nav_url":        sales_nav_url,
                "phantombuster_status": "building_url",
            }).eq("id", row["id"]).execute()
            advanced += 1
            logger.info("contact_gaps: phase1 complete for %s → org_id %s", row["domain"], org_id)
        except Exception as exc:
            logger.error("contact_gaps: poll_phase1 error for %s: %s", row["domain"], exc)

    return advanced


# ── Phase 2 — Sales Navigator Search Export ────────────────────────────────────

def run_phase2() -> int:
    """Launch Sales Navigator Search Export with up to PHASE2_BATCH_SIZE URLs in ONE
    container, if no other PB container is in flight.

    PB processes the 5 URLs sequentially inside a single container (~5 min total
    instead of ~15 min spread across 5 separate launches), freeing the shared
    parallel slot for Phase 1 launches sooner.

    The 5 contact_gaps rows share the same phantom_id; poll_phase2 demuxes results
    by the `companyId` field returned per scraped profile."""
    in_flight = fetch_all(
        "contact_gaps", "id",
        filters=[("in_", "phantombuster_status", ["extracting_company", "scraping_contacts"])],
        limit=1,
    )
    if in_flight:
        logger.info("contact_gaps: phase2 skipped — another container in flight")
        return 0

    rows = fetch_all(
        "contact_gaps", "id,domain,company_name,market,batch_number,sales_nav_url,linkedin_company_id",
        filters=[("eq", "phantombuster_status", "building_url")],
        limit=PHASE2_BATCH_SIZE,
    )
    rows = [r for r in rows if r.get("sales_nav_url")]
    if not rows:
        return 0

    # Wait until we have a full batch of 5 before firing Phase 2 — but only if
    # more pending rows could still produce more building_url rows. This is the
    # core trick that lets Phase 1 run 5x before Phase 2 hogs the parallel slot.
    if len(rows) < PHASE2_BATCH_SIZE:
        pending = fetch_all("contact_gaps", "id",
                            filters=[("eq", "phantombuster_status", "pending")], limit=1)
        if pending:
            logger.info(
                "contact_gaps: phase2 holding — only %d building_url rows ready, "
                "letting phase1 accumulate to %d", len(rows), PHASE2_BATCH_SIZE,
            )
            return 0
        # No more pending — drain the partial batch (last-minute stragglers).

    sb = get_supabase()
    agent_id = os.environ["PHANTOMBUSTER_SALES_NAV_ID"]
    ids = ",".join(str(r["id"]) for r in rows)
    csv_url = f"{PUBLIC_API_BASE}/pipelines/contact-gaps/sales-nav-csv?ids={ids}"

    try:
        container_id = launch_agent(agent_id, {
            "inputType":                "spreadsheetUrl",
            "spreadsheetUrl":           csv_url,
            "numberOfProfiles":         25,
            "numberOfResultsPerSearch": 25,
            "numberOfLinesPerLaunch":   PHASE2_BATCH_SIZE,
            "removeDuplicateProfiles":  False,
            "csvName":                  f"phase2_batch_{int(__import__('time').time())}",
        })
        sb.table("contact_gaps").update({
            "phantombuster_status": "scraping_contacts",
            "phantom_id": container_id,
            "phase": 2,
        }).in_("id", [r["id"] for r in rows]).execute()
        logger.info(
            "contact_gaps: phase2 batch launched (%d rows, container %s): %s",
            len(rows), container_id, [r["domain"] for r in rows],
        )
        return 1
    except Exception as exc:
        logger.error("contact_gaps: phase2 batch launch failed: %s", exc)
        sb.table("contact_gaps").update({"phantombuster_status": "failed"}).in_(
            "id", [r["id"] for r in rows]
        ).execute()
        return 0


def poll_phase2() -> int:
    """Check Phase 2 containers.  Multiple contact_gaps rows may share the same
    phantom_id (batched launch), so we group by phantom_id, fetch each container
    once, and demux the scraped profiles back to their company via the row's
    `companyId` field (= linkedin_company_id)."""
    rows = fetch_all(
        "contact_gaps",
        "id,domain,company_name,market,batch_number,phantom_id,linkedin_company_id",
        filters=[("eq", "phantombuster_status", "scraping_contacts")],
    )
    if not rows:
        return 0

    # Group rows by container so we hit PB once per container, not once per row.
    by_container: dict[str, list[dict]] = {}
    for r in rows:
        by_container.setdefault(r["phantom_id"], []).append(r)

    sb = get_supabase()
    completed = 0

    for container_id, gap_rows in by_container.items():
        try:
            container = get_container(container_id)
            if not is_finished(container):
                continue
            if is_error(container):
                sb.table("contact_gaps").update({"phantombuster_status": "failed"}).in_(
                    "id", [g["id"] for g in gap_rows]
                ).execute()
                logger.warning("contact_gaps: phase2 container %s errored", container_id)
                continue

            result_rows = get_result_rows({**container, "id": container_id})
            # Demux scraped profiles back to companies by matching companyId
            by_company: dict[str, list[dict]] = {}
            for pb in result_rows:
                cid = str(pb.get("companyId") or "")
                if cid:
                    by_company.setdefault(cid, []).append(pb)

            now_iso = datetime.now(timezone.utc).isoformat()
            for gap in gap_rows:
                org_id = str(gap.get("linkedin_company_id") or "")
                pb_rows_for_company = by_company.get(org_id, [])
                contacts = [_map_contact(r, gap) for r in pb_rows_for_company if r]
                contacts = [c for c in contacts if c.get("linkedin_url")]

                if not contacts:
                    sb.table("contact_gaps").update({
                        "phantombuster_status": "no_contacts_found",
                        "contacts_found":       0,
                        "completed_at":         now_iso,
                    }).eq("id", gap["id"]).execute()
                    _update_campaign_counts(gap["domain"], gap["batch_number"], 0, "none")
                    logger.info("contact_gaps: no contacts found for %s", gap["domain"])
                    continue

                for contact in contacts:
                    sb.table("phantombuster_contacts").upsert(
                        contact, on_conflict="domain,linkedin_url,batch_number"
                    ).execute()
                sb.table("contact_gaps").update({
                    "phantombuster_status": "completed",
                    "contacts_found":       len(contacts),
                    "completed_at":         now_iso,
                }).eq("id", gap["id"]).execute()
                _update_campaign_counts(gap["domain"], gap["batch_number"], len(contacts), "linkedin")
                completed += 1
                logger.info("contact_gaps: completed for %s → %d contacts", gap["domain"], len(contacts))
        except Exception as exc:
            logger.error("contact_gaps: poll_phase2 error on container %s: %s", container_id, exc)

    return completed


def _map_contact(pb_row: dict, gap_row: dict) -> dict:
    """Shape a PB Sales Nav result row to match phantombuster_contacts columns."""
    return {
        "domain":       gap_row["domain"],
        "company_name": gap_row.get("company_name"),
        "market":       gap_row.get("market"),
        "batch_number": gap_row.get("batch_number"),
        "email":        pb_row.get("email"),
        "first_name":   pb_row.get("firstName") or pb_row.get("first_name"),
        "last_name":    pb_row.get("lastName")  or pb_row.get("last_name"),
        "job_title":    pb_row.get("title") or pb_row.get("occupation") or pb_row.get("currentJob"),
        # Prefer regular LinkedIn profile URLs over Sales Nav lead URLs (which can't be
        # used outside Sales Navigator). PB returns both for each row.
        "linkedin_url": (
            pb_row.get("linkedInProfileUrl")
            or pb_row.get("defaultProfileUrl")
            or pb_row.get("profileUrl")
            or pb_row.get("linkedinUrl")
            or pb_row.get("linkedin_url")
        ),
        "raw":          pb_row,
    }


# ── FastAPI endpoints ──────────────────────────────────────────────────────────

async def _run_contact_gaps_bg(batch_number: int) -> None:
    try:
        gaps     = detect_gaps(batch_number)
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


@router.get("/pipelines/contact-gaps/sales-nav-csv")
async def sales_nav_csv(ids: str):
    """Public CSV endpoint that PhantomBuster's Sales Nav Search Export fetches when
    we batch 5 URLs per launch (inputType=spreadsheetUrl).  Takes a comma-separated
    list of contact_gaps row ids and returns a single-column CSV of their
    sales_nav_urls.

    No auth — PB fetches anonymously.  The URLs themselves are non-secret
    LinkedIn Sales Navigator search URLs."""
    from fastapi.responses import Response
    id_list = [s.strip() for s in (ids or "").split(",") if s.strip()]
    if not id_list:
        return Response("salesNavigatorSearchUrl\n", media_type="text/csv")
    rows = fetch_all(
        "contact_gaps", "id,sales_nav_url",
        filters=[("in_", "id", id_list)],
    )
    # Preserve the requested order so PB processes them deterministically
    by_id = {str(r["id"]): r for r in rows}
    lines = ["salesNavigatorSearchUrl"]
    for rid in id_list:
        r = by_id.get(rid)
        if r and r.get("sales_nav_url"):
            lines.append(r["sales_nav_url"])
    return Response("\n".join(lines) + "\n", media_type="text/csv")


@router.post("/pipelines/contact-gaps/run-latest")
async def run_contact_gaps_latest(background_tasks: BackgroundTasks):
    """Cron-friendly: trigger contact-gaps for the most recent batch_number in
    campaign_batches.  Used by the day-2 monthly cron."""
    rows = fetch_all("campaign_batches", "batch_number",
                     order_by=[("batch_number", True)], limit=1)
    if not rows:
        return {"status": "no_batches"}
    batch_number = rows[0]["batch_number"]
    background_tasks.add_task(_run_contact_gaps_bg, batch_number)
    return {"status": "started", "batch_number": batch_number}


async def _post_digest_bg() -> None:
    """Daily digest: post one Slack message summarising progress on the latest batch."""
    from datetime import datetime, timedelta, timezone
    from collections import Counter

    batches = fetch_all("campaign_batches", "batch_number",
                        order_by=[("batch_number", True)], limit=1)
    if not batches:
        return
    bn = batches[0]["batch_number"]

    gaps = fetch_all("contact_gaps", "phantombuster_status,completed_at",
                     filters=[("eq", "batch_number", bn)])
    status_counts = Counter(g["phantombuster_status"] for g in gaps)
    total = len(gaps)
    terminal = sum(status_counts.get(s, 0) for s in
                   ("completed", "no_contacts_found", "failed", "subsidiary_skipped"))
    in_flight = sum(status_counts.get(s, 0) for s in
                    ("extracting_company", "scraping_contacts"))
    pending = status_counts.get("pending", 0)

    # Last 24h throughput
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    completed_last_24h = sum(
        1 for g in gaps
        if g.get("completed_at") and
        datetime.fromisoformat(g["completed_at"].replace("Z", "+00:00")) > cutoff
    )

    pbc_rows = fetch_all("phantombuster_contacts",
                         "relevance_score,scored_at,promoted_to_sourced_contacts",
                         filters=[("eq", "batch_number", bn)])
    scraped_total = len(pbc_rows)
    scored        = sum(1 for r in pbc_rows if r.get("scored_at"))
    promoted      = sum(1 for r in pbc_rows if r.get("promoted_to_sourced_contacts"))
    relevant_pct  = round(promoted / scored * 100) if scored else 0

    pct = round(terminal / total * 100) if total else 0
    eta_days = round(pending / completed_last_24h) if completed_last_24h else None
    eta_str  = f"~{eta_days} days" if eta_days else "n/a (no recent throughput)"

    msg = (
        f"📊 *Contact-gap progress — batch #{bn}*\n"
        f"• Companies: *{terminal}/{total}* done ({pct}%) — {in_flight} in flight, {pending} pending\n"
        f"• Throughput (24h): {completed_last_24h} companies — ETA: {eta_str}\n"
        f"• PB contacts scraped: {scraped_total} — scored: {scored} — promoted: {promoted} ({relevant_pct}% relevant)\n"
        f"• Failed/skipped: {status_counts.get('failed', 0) + status_counts.get('subsidiary_skipped', 0)}"
    )
    await notify(msg)


@router.post("/pipelines/contact-gaps/digest")
async def contact_gaps_digest(background_tasks: BackgroundTasks):
    """Daily Slack digest of contact-gap pipeline progress on the latest batch."""
    background_tasks.add_task(_post_digest_bg)
    return {"status": "started"}


@router.post("/pipelines/contact-gaps/poll")
async def poll_contact_gaps():
    """Advance all in-flight PhantomBuster jobs AND launch the next pending one.
    Run every 30 min via Railway cron.

    Sequencing inside a single call:
      1. poll_phase1 — drain any finished Phase 1 containers to building_url
      2. run_phase2  — if no in-flight, launch ONE Sales Nav search
      3. poll_phase2 — drain any finished Phase 2 containers (write contacts)
      4. run_phase1  — if no in-flight + under daily cap, launch ONE Phase 1
    """
    p1_done       = poll_phase1()
    p2_launched   = run_phase2()
    p2_done       = poll_phase2()
    p1_launched   = run_phase1_for_latest_batch()
    logger.info(
        "contact_gaps/poll: p1_done=%d p2_launched=%d p2_done=%d p1_launched=%d",
        p1_done, p2_launched, p2_done, p1_launched,
    )
    return {
        "phase1_advanced":   p1_done,
        "phase2_launched":   p2_launched,
        "phase2_completed":  p2_done,
        "phase1_launched":   p1_launched,
    }


def run_phase1_for_latest_batch() -> int:
    """Cron-friendly run_phase1: resolves the latest batch_number itself."""
    batches = fetch_all("campaign_batches", "batch_number",
                        order_by=[("batch_number", True)], limit=1)
    if not batches:
        return 0
    return run_phase1(batches[0]["batch_number"])
