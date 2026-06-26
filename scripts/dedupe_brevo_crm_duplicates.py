"""Find and remove duplicate Brevo CRM company records.

Background: The 2026-06-25 mass push duplicated ~6,000 CRM records that
already existed from the 2026-06-23 push. Cause: the Daily Pipeline cron's
run_prioritize upsert wiped priority_tam.brevo_company_id overnight by
overwriting with NULL from qualified_tam_v2. Today's crm_sync saw NULL IDs
and POSTed every affected row as if new.

This script repairs by:
  1. Iterate priority_tam rows where brevo_sync_method='POST'
  2. For each row's domain, query Brevo CRM by attributes.website
  3. If multiple records exist:
     - Keep the OLDEST (yesterday's original record, RevOps may have actioned)
     - DELETE the newer duplicates via DELETE /v3/companies/{id}
     - Update priority_tam.brevo_company_id to the oldest ID
  4. If single record: no duplicate, leave alone

Usage:
    source .env && python scripts/dedupe_brevo_crm_duplicates.py --dry-run
    source .env && python scripts/dedupe_brevo_crm_duplicates.py --limit 20
    source .env && python scripts/dedupe_brevo_crm_duplicates.py            # FULL RUN
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.client import fetch_all, get_supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
for noisy in ("httpx", "httpcore", "hpack"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

BREVO_CRM_BASE_URL = "https://api.brevo.com/v3"
_MAX_INFLIGHT = 8
_HTTP_TIMEOUT = 20.0


async def search_by_website(client, website):
    """Return all Brevo CRM company records with this website, sorted oldest-first."""
    headers = {"api-key": os.environ["BREVO_CRM_API_KEY"]}
    params = {"filters": json.dumps({"attributes.website": website})}

    for attempt, wait in enumerate([0, 1, 2, 4]):
        if wait:
            await asyncio.sleep(wait)
        resp = await client.get(
            f"{BREVO_CRM_BASE_URL}/companies",
            headers=headers, params=params, timeout=_HTTP_TIMEOUT,
        )
        if resp.status_code in (429, 500) and attempt < 3:
            continue
        resp.raise_for_status()
        items = resp.json().get("items", []) or []
        # Sort by created_at ascending — oldest first
        items.sort(key=lambda i: (i.get("attributes") or {}).get("created_at") or "")
        return items
    return []


async def delete_company(client, company_id):
    headers = {"api-key": os.environ["BREVO_CRM_API_KEY"]}
    resp = await client.delete(
        f"{BREVO_CRM_BASE_URL}/companies/{company_id}",
        headers=headers, timeout=_HTTP_TIMEOUT,
    )
    return resp.status_code in (200, 204), resp.status_code, resp.text[:200]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Inspect duplicates without deleting or writing back.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N priority_tam POST rows (smoke testing).")
    args = parser.parse_args()

    rows = fetch_all(
        "priority_tam",
        "id, domain, market, company_name, brevo_company_id, brevo_sync_method",
        [("eq", "brevo_sync_method", "POST")],
        limit=args.limit,
    )
    logger.info("Loaded %d priority_tam POST rows for inspection", len(rows))

    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    counts = {
        "no_record":     0,  # nothing in CRM (orphan — shouldn't happen)
        "single":        0,  # one record, no duplicate
        "duplicate":     0,  # multiple records, will be deduped
        "deleted":       0,  # individual CRM records deleted
        "delete_failed": 0,  # delete API call failed
        "linked_back":   0,  # priority_tam.brevo_company_id corrected
        "errors":        0,
    }
    sample_duplicates = []

    sb = get_supabase()

    async with httpx.AsyncClient() as client:
        async def _one(row):
            try:
                async with sem:
                    matches = await search_by_website(client, row["domain"])
                    if not matches:
                        counts["no_record"] += 1
                        return
                    if len(matches) == 1:
                        counts["single"] += 1
                        # If priority_tam's ID doesn't match the only existing CRM record,
                        # fix it (silent re-link, no delete needed).
                        only_id = matches[0]["id"]
                        if row.get("brevo_company_id") != only_id and not args.dry_run:
                            sb.table("priority_tam").update({"brevo_company_id": only_id}).eq("id", row["id"]).execute()
                            counts["linked_back"] += 1
                        return

                    counts["duplicate"] += 1
                    oldest = matches[0]
                    to_delete = matches[1:]
                    if len(sample_duplicates) < 10:
                        sample_duplicates.append({
                            "domain": row["domain"],
                            "company_name": row.get("company_name"),
                            "kept_id": oldest["id"],
                            "delete_ids": [m["id"] for m in to_delete],
                        })

                    if not args.dry_run:
                        for m in to_delete:
                            ok, status, body = await delete_company(client, m["id"])
                            if ok:
                                counts["deleted"] += 1
                            else:
                                counts["delete_failed"] += 1
                                logger.warning("Delete %s failed: %d %s", m["id"], status, body)

                        # Re-link priority_tam to the oldest (kept) record
                        sb.table("priority_tam").update(
                            {"brevo_company_id": oldest["id"]}
                        ).eq("id", row["id"]).execute()
                        counts["linked_back"] += 1

                done = sum([counts["no_record"], counts["single"], counts["duplicate"]])
                if done % 250 == 0:
                    logger.info("Progress: %d/%d processed (duplicate=%d, single=%d, no_record=%d)",
                                done, len(rows), counts["duplicate"], counts["single"], counts["no_record"])
            except Exception as exc:
                counts["errors"] += 1
                logger.exception("Error processing %s", row.get("domain"))

        await asyncio.gather(*[_one(r) for r in rows])

    print()
    print("=" * 60)
    print(f"Mode:                 {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"Total POST rows:      {len(rows)}")
    print(f"Single CRM record:    {counts['single']}")
    print(f"Duplicate clusters:   {counts['duplicate']}")
    print(f"No CRM record found:  {counts['no_record']}")
    print(f"Deleted (newer):      {counts['deleted']}")
    print(f"Delete failed:        {counts['delete_failed']}")
    print(f"Re-linked priority_tam: {counts['linked_back']}")
    print(f"Errors:               {counts['errors']}")
    print("=" * 60)
    if sample_duplicates:
        print("\nSample duplicates (up to 10):")
        for s in sample_duplicates:
            print(f"  {s['domain']:35s} keep={s['kept_id']}  delete={s['delete_ids']}")


if __name__ == "__main__":
    asyncio.run(main())
