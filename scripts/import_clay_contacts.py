"""Import a Clay-sourced contacts CSV into sourced_contacts.

Reusable across batches — the CSV column mapping below works for any Clay
export that follows the standard structure (Company Domain, Work email,
LinkedIn Profile, etc.). Set BATCH_NUMBER at the top of this file before
each run so contacts are tagged correctly.

Usage:
    python scripts/import_clay_contacts.py path/to/clay_export.csv --dry-run
    python scripts/import_clay_contacts.py path/to/clay_export.csv

Per-row uniqueness in sourced_contacts is keyed by normalised `linkedin_url`
(see migration 037). The CSV LinkedIn Profile URLs are lowercased and stripped
of scheme + "www." + trailing slash before insert so cross-source dedupe
(Clay vs PhantomBuster) collapses to a single canonical handle.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

# Make repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase  # noqa: E402
from utils.linkedin import normalise_linkedin_url  # noqa: E402

BATCH_NUMBER = 2

# Clay CSV → sourced_contacts column mapping.
# Batch 2's Clay table renames a couple of columns vs batch 1:
#   "Work email"       → "Preferred Email"
#   "Relevance Score"  → "Job Title Relevance Score relevance Score"
#   "Reasoning"        → "Job Title Relevance Score reasoning"
# Email Provider column is no longer exported.
COLUMN_MAP = {
    "domain":              "Company Domain",
    "company_name":        "Company Name",
    "email":               "Preferred Email",
    "first_name":          "First Name",
    "last_name":           "Last Name",
    "job_title":           "Job Title",
    "linkedin_url":        "LinkedIn Profile",
    "market":              "Market",
    "relevance_score":     "Job Title Relevance Score relevance Score",
    "relevance_reasoning": "Job Title Relevance Score reasoning",
}


def _coerce_int(val: str | None) -> int | None:
    val = (val or "").strip()
    if not val:
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def map_row(csv_row: dict) -> dict | None:
    mapped: dict = {"batch_number": BATCH_NUMBER, "source": "clay"}
    for db_col, csv_col in COLUMN_MAP.items():
        val = (csv_row.get(csv_col) or "").strip() or None
        mapped[db_col] = val

    # Skip rows that can't be deduped or attributed
    if not mapped.get("linkedin_url") or not mapped.get("domain"):
        return None

    # Persist location + country + the raw CSV row in the jsonb `raw` column.
    # Downstream enrichment (e.g. scripts/enrich_gifting_addresses.py) reads
    # raw.location as the LinkedIn city hint — same key PB Sales Nav uses on
    # its own contacts. Backfill 2026-07-02 added this after 172 batch #2
    # contacts landed with raw=NULL because Location wasn't mapped here.
    mapped["raw"] = {
        "location":      (csv_row.get("Location") or "").strip(),
        "country":       (csv_row.get("Country")  or "").strip(),
        "clay_full_row": csv_row,
    }

    mapped["linkedin_url"]    = normalise_linkedin_url(mapped["linkedin_url"])
    mapped["relevance_score"] = _coerce_int(mapped.get("relevance_score"))
    return mapped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate mapping and print sample rows; do not write.")
    args = parser.parse_args()

    if not args.csv_path.exists():
        sys.exit(f"CSV not found: {args.csv_path}")

    with args.csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("CSV is empty")

    print(f"CSV headers: {list(rows[0].keys())}")
    print(f"Total CSV rows: {len(rows)}")

    mapped_rows: list[dict] = []
    skipped_no_li = 0
    skipped_no_domain = 0
    for r in rows:
        if not (r.get("LinkedIn Profile") or "").strip():
            skipped_no_li += 1
            continue
        if not (r.get("Company Domain") or "").strip():
            skipped_no_domain += 1
            continue
        m = map_row(r)
        if m is not None:
            mapped_rows.append(m)

    print(f"  mappable: {len(mapped_rows)}")
    print(f"  skipped (no LinkedIn URL): {skipped_no_li}")
    print(f"  skipped (no domain):       {skipped_no_domain}")

    # Detect duplicate normalised linkedin_urls inside the CSV itself
    by_li: dict[str, int] = {}
    for m in mapped_rows:
        by_li[m["linkedin_url"]] = by_li.get(m["linkedin_url"], 0) + 1
    dupes_in_csv = sum(1 for c in by_li.values() if c > 1)
    if dupes_in_csv:
        print(f"  ⚠️  {dupes_in_csv} linkedin_url(s) appear more than once in the CSV — "
              f"last occurrence wins on upsert")

    if args.dry_run:
        print("\nFirst 3 mapped rows:")
        for m in mapped_rows[:3]:
            print({k: v for k, v in m.items() if k != "relevance_reasoning"})
        return

    sb = get_supabase()
    inserted = 0
    failed   = 0
    for m in mapped_rows:
        try:
            sb.table("sourced_contacts").upsert(
                m, on_conflict="linkedin_url",
            ).execute()
            inserted += 1
        except Exception as exc:
            print(f"  ❌ {m.get('linkedin_url')}: {exc}")
            failed += 1

    print(f"\n✅ Import complete: {inserted} upserted, {failed} failed")


if __name__ == "__main__":
    main()
