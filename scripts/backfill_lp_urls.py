"""Backfill personalised_lp_url for sourced_contacts whose LP minting failed
during the original content batch (timeout / 502 from the LP API).

Re-runs lp_generator.fetch_company_lp for each unique missing domain (cache-
first, so it only fires API calls for domains not already in
company_lp_cache), then patches each affected contact's outbound_content
jsonb in place.

Safe to re-run: contacts whose LP is now present are skipped on the next
invocation. Failures (still-timing-out domains) leave the URL empty and the
script can be run again later.

Usage:
    source .env && python scripts/backfill_lp_urls.py [--dry-run]
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
for noisy in ("httpx", "httpcore", "hpack", "anthropic"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from db.client import get_supabase, fetch_all  # noqa: E402
from pipelines.lp_generator import fetch_many as fetch_lp_many  # noqa: E402

logger = logging.getLogger("backfill_lp_urls")


def _is_missing_lp(oc: dict | None) -> bool:
    if not oc:
        return False  # no content at all → out of scope for this backfill
    return not (oc.get("personalised_lp_url") or "").strip()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Identify missing LPs and show counts, but don't mint or update.")
    args = parser.parse_args()

    sb = get_supabase()

    # Pull all batch-1 contacts; filter for those with content generated in
    # Python (fetch_all's getattr-based filter mechanism can't chain
    # supabase-py's two-call `not_.is_("col", "null")` API).
    logger.info("backfill: loading batch-1 contacts...")
    all_rows = fetch_all(
        "sourced_contacts",
        "id, domain, market, company_name, outbound_content, content_generated_at",
        [("eq", "batch_number", 1)],
    )
    rows = [r for r in all_rows if r.get("content_generated_at")]
    logger.info("backfill: %d / %d contacts have generated content",
                len(rows), len(all_rows))

    missing = [r for r in rows if _is_missing_lp(r.get("outbound_content"))]
    logger.info("backfill: %d contacts are missing personalised_lp_url", len(missing))

    if not missing:
        logger.info("backfill: nothing to do")
        return

    # Unique domains needing mints
    by_domain: dict[str, list[dict]] = {}
    for r in missing:
        d = (r.get("domain") or "").strip().lower()
        if d:
            by_domain.setdefault(d, []).append(r)

    domains = list(by_domain.keys())
    logger.info("backfill: %d unique domains across the %d missing contacts",
                len(domains), len(missing))

    # Enrich with priority_tam (need vertical/market/esp for the LP API)
    company_rows = fetch_all(
        "priority_tam",
        "domain, market, company_name, vertical, esp_detected",
        [("in_", "domain", domains)],
    )
    company_map = {r["domain"]: r for r in company_rows}

    lp_inputs: list[dict] = []
    skipped_no_company = 0
    for d in domains:
        company = company_map.get(d, {})
        contact_market = by_domain[d][0].get("market")
        lp_inputs.append({
            "domain":       d,
            "company_name": company.get("company_name") or by_domain[d][0].get("company_name") or "",
            "industry":     company.get("vertical"),
            "market":       contact_market or company.get("market"),
            "esp":          company.get("esp_detected"),
        })
        if not company.get("vertical"):
            skipped_no_company += 1
    if skipped_no_company:
        logger.warning("backfill: %d domains have no vertical in priority_tam — lp_generator will skip those",
                       skipped_no_company)

    if args.dry_run:
        logger.info("backfill: dry-run, not minting. First 5 inputs:")
        for inp in lp_inputs[:5]:
            print(f"  {inp}")
        return

    # Fan out LP minting (cache-first; for the failed domains the cache is
    # empty so this will trigger API calls)
    logger.info("backfill: minting LPs for %d domains (this may take ~%d min)...",
                len(lp_inputs), len(lp_inputs) * 40 // 15 // 60 + 1)
    lp_map = await fetch_lp_many(lp_inputs)
    logger.info("backfill: minted %d / %d LPs", len(lp_map), len(lp_inputs))

    # Patch each affected contact
    patched = 0
    still_missing = 0
    for d, contacts in by_domain.items():
        url = lp_map.get(d, "")
        if not url:
            still_missing += len(contacts)
            continue
        for c in contacts:
            oc = dict(c["outbound_content"] or {})
            oc["personalised_lp_url"] = url
            sb.table("sourced_contacts").update({
                "outbound_content": oc,
            }).eq("id", c["id"]).execute()
            patched += 1

    logger.info(
        "backfill: done — %d contacts patched, %d still missing (LP API still failing for those domains)",
        patched, still_missing,
    )


if __name__ == "__main__":
    asyncio.run(main())
