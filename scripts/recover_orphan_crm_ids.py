"""Recover Brevo CRM IDs for POST-path rows pushed BEFORE the writeback was added.

The 2026-06-22 trial pushed 100 rows via POST to Brevo CRM and DID NOT write
the returned CRM ID back to priority_tam. Those rows are now in CRM but their
priority_tam.brevo_company_id is still NULL — so a mass push would duplicate
them. This script:

1. Reads data/crm_sync_2026-06-22_trial200.csv
2. Filters to mode='POST' rows
3. For each row whose priority_tam STILL has no brevo_company_id (skip ones
   we manually linked yesterday)
4. Searches Brevo CRM by attributes.website = <domain> + disambiguates by name
5. Writes the matched CRM id + brevo_sync_method='POST' back to priority_tam

Usage:
    source .env && python scripts/recover_orphan_crm_ids.py
"""
import asyncio
import csv
import json
import logging
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.client import get_supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
for noisy in ("httpx", "httpcore", "hpack"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

CSV_PATH = Path("data/crm_sync_2026-06-22_trial200.csv")
BREVO_CRM_BASE_URL = "https://api.brevo.com/v3"
_MAX_INFLIGHT = 10


async def search_companies_by_website(client, website):
    """Return all Brevo CRM companies matching attributes.website = <value>."""
    url = f"{BREVO_CRM_BASE_URL}/companies"
    headers = {"api-key": os.environ["BREVO_CRM_API_KEY"]}
    params = {"filters": json.dumps({"attributes.website": website})}

    for attempt, wait in enumerate([0, 1, 2, 4]):
        if wait:
            await asyncio.sleep(wait)
        resp = await client.get(url, headers=headers, params=params, timeout=15.0)
        if resp.status_code in (429, 500) and attempt < 3:
            continue
        resp.raise_for_status()
        return resp.json().get("items", []) or []
    return []


def _item_name(item):
    """Brevo CRM returns the company name either at the root or under attributes."""
    return item.get("name") or (item.get("attributes") or {}).get("name") or ""


def disambiguate(items, expected_name):
    """Pick the company whose name matches what we POSTed. Returns id or None."""
    if not items:
        return None
    if len(items) == 1:
        return items[0].get("id")
    # Try exact name match
    for item in items:
        if _item_name(item).strip() == (expected_name or "").strip():
            return item.get("id")
    # No safe match — refuse to guess
    return None


def write_back(domain, market, company_name, brevo_id):
    sb = get_supabase()
    sb.table("priority_tam").update({
        "brevo_company_id":  brevo_id,
        "brevo_sync_method": "POST",
    }).eq("domain", domain).eq("market", market).eq("company_name", company_name).execute()


async def main():
    if not CSV_PATH.exists():
        logger.error("CSV not found: %s", CSV_PATH)
        sys.exit(1)

    # Load POST rows from CSV
    csv_rows = []
    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["mode"] == "POST" and row["domain"]:
                csv_rows.append({
                    "domain":       row["domain"],
                    "market":       row["market"],
                    "company_name": row["company_name"],
                })

    logger.info("Loaded %d POST-mode rows from CSV", len(csv_rows))

    # Skip rows that already have brevo_company_id linked back
    sb = get_supabase()
    todo = []
    skipped = 0
    for r in csv_rows:
        existing = (
            sb.table("priority_tam").select("brevo_company_id")
            .eq("domain", r["domain"]).eq("market", r["market"])
            .eq("company_name", r["company_name"]).execute().data
        )
        if existing and (existing[0].get("brevo_company_id") or "").strip():
            skipped += 1
        else:
            todo.append(r)
    logger.info("Already linked: %d  |  To recover: %d", skipped, len(todo))

    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    found = 0
    not_found = []
    ambiguous = []
    failed = []

    async with httpx.AsyncClient() as client:
        async def _one(row):
            nonlocal found
            async with sem:
                try:
                    items = await search_companies_by_website(client, row["domain"])
                    brevo_id = disambiguate(items, row["company_name"])
                    if brevo_id:
                        write_back(row["domain"], row["market"], row["company_name"], brevo_id)
                        found += 1
                    elif items:
                        ambiguous.append({"row": row, "candidates": len(items)})
                    else:
                        not_found.append(row)
                except Exception as exc:
                    failed.append({"row": row, "error": str(exc)[:200]})

        await asyncio.gather(*[_one(r) for r in todo])

    print()
    print("=" * 70)
    print(f"Recovered (linked back):      {found:>4} / {len(todo)}")
    print(f"Not found in Brevo CRM:       {len(not_found):>4}")
    print(f"Ambiguous (multiple matches): {len(ambiguous):>4}")
    print(f"Errors:                       {len(failed):>4}")
    print("=" * 70)
    if not_found:
        print("\nDomains with no Brevo CRM match (will CREATE on next mass push):")
        for r in not_found[:20]:
            print(f"  - {r['domain']}  ({r['company_name']})")
        if len(not_found) > 20:
            print(f"  ... and {len(not_found) - 20} more")
    if ambiguous:
        print("\nDomains with multiple Brevo CRM candidates (no exact name match):")
        for a in ambiguous[:10]:
            print(f"  - {a['row']['domain']}  ({a['row']['company_name']})  [{a['candidates']} candidates]")
    if failed:
        print("\nErrors:")
        for f in failed[:10]:
            print(f"  - {f['row']['domain']}: {f['error']}")


if __name__ == "__main__":
    asyncio.run(main())
