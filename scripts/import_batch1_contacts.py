"""
One-shot script: import batch 1 contacts from CSV → sourced_contacts.

Usage:
    python scripts/import_batch1_contacts.py path/to/contacts.csv [--dry-run]

First run with --dry-run to print CSV headers and first row, then update
COLUMN_MAP below to match the actual field names in your CSV.
"""
import argparse
import csv
import os
import sys

from supabase import create_client

BATCH_NUMBER = 1

# ── Update this map once you share the CSV ────────────────────────────────────
# Format: "sourced_contacts column" → "CSV header"
# Set value to None to skip a column.
COLUMN_MAP = {
    "domain":       "domain",          # update if different
    "company_name": "company_name",
    "market":       "market",
    "email":        "email",
    "first_name":   "first_name",
    "last_name":    "last_name",
    "job_title":    "job_title",
    "seniority":    "seniority",
    "linkedin_url": "linkedin_url",
}
# ─────────────────────────────────────────────────────────────────────────────


def map_row(csv_row: dict) -> dict:
    mapped = {"batch_number": BATCH_NUMBER, "source": "clay"}
    for db_col, csv_col in COLUMN_MAP.items():
        if csv_col and csv_col in csv_row:
            val = csv_row[csv_col].strip() or None
            mapped[db_col] = val
    return mapped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print headers + first 3 rows, don't write to DB")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("CSV is empty")
        sys.exit(1)

    print(f"CSV headers: {list(rows[0].keys())}")
    print(f"Total rows: {len(rows)}")

    if args.dry_run:
        print("\nFirst 3 mapped rows:")
        for r in rows[:3]:
            print(map_row(r))
        print("\nUpdate COLUMN_MAP in this script if the mapping looks wrong, then run without --dry-run")
        return

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )

    inserted = 0
    skipped  = 0
    for row in rows:
        mapped = map_row(row)
        if not mapped.get("domain"):
            skipped += 1
            continue
        try:
            sb.table("sourced_contacts").upsert(mapped, on_conflict="domain,email").execute()
            inserted += 1
        except Exception as exc:
            print(f"  ERROR on row {row}: {exc}")
            skipped += 1

    print(f"\nDone — inserted/updated: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    main()
