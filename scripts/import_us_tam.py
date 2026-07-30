"""Import the US TAM CSV into sourced_tam_v2 + qualified_tam_v2.

Different from a normal Clay TAM ingest: this CSV comes pre-scored (ESP
detected, tech score, firmo score, priority score, tier, routing action)
by an external process — so we bypass the qualification pipeline entirely
and write the values verbatim, marking `qualification_checked=true` and
`crm_checked=true` on sourced_tam_v2 so the daily pipeline skips them.

What still needs to run after this import:
  /pipelines/enrich  →  fills account_fit_score + account_narrative + vertical
                        (Claude Batch API on all qualified_tam_v2 rows)
  /pipelines/prioritize  →  promotes account_fit_score >= 3 into priority_tam

Column mapping (CSV → tables):
  Name              → company_name          (both tables)
  Domain            → domain (lowercased)   (both tables)
  Size              → employee_range        (both tables)
  Country           → country ("United States")
  ESP Detected      → esp_detected          (qualified_tam_v2)
  Tech Score        → esp_score             (qualified_tam_v2)
  Brevo CRM ID      → brevo_company_id      (both tables)
  full CSV row      → raw jsonb             (sourced_tam_v2 only)

Dedupe rule: 6,931 rows collapse to 5,696 unique domains. When the same
domain appears multiple times (Marriott properties, hotel chains, etc.)
we keep the row with the highest Priority Score.

Exclusion rule: rows tagged Routing Action='Exclude' land in sourced_tam_v2
(for record-keeping) but NOT in qualified_tam_v2, so they never reach
Claude enrichment or the priority queue.

Usage:
    python scripts/import_us_tam.py path/to/csv --dry-run
    python scripts/import_us_tam.py path/to/csv
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase  # noqa: E402

MARKET  = "US"
COUNTRY = "United States"

CSV_COL = {
    "domain":           "Domain",
    "company_name":     "Name",
    "employee_range":   "Size",
    "esp_detected":     "ESP Detected",
    "esp_score":        "Tech Score",
    "brevo_company_id": "Brevo CRM ID",
    "priority_score":   "Priority Score",
    "tier":             "Tier",
    "routing_action":   "Routing Action",
}


def _norm_domain(d: str) -> str:
    return (d or "").strip().lower()


def _int_or_none(v: str) -> int | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def _str_or_none(v: str) -> str | None:
    v = (v or "").strip()
    return v or None


def dedupe_by_domain(rows: list[dict]) -> list[dict]:
    """Keep the row with the highest Priority Score per domain."""
    best: dict[str, dict] = {}
    for r in rows:
        d = _norm_domain(r.get(CSV_COL["domain"], ""))
        if not d:
            continue
        ps = _int_or_none(r.get(CSV_COL["priority_score"], "")) or 0
        current = best.get(d)
        if current is None or ps > (_int_or_none(current.get(CSV_COL["priority_score"], "")) or 0):
            best[d] = r
    return list(best.values())


def map_to_sourced(csv_row: dict) -> dict:
    return {
        "domain":                 _norm_domain(csv_row[CSV_COL["domain"]]),
        "market":                 MARKET,
        "company_name":           _str_or_none(csv_row[CSV_COL["company_name"]]),
        "employee_range":         _str_or_none(csv_row[CSV_COL["employee_range"]]),
        "country":                COUNTRY,
        "brevo_company_id":       _str_or_none(csv_row[CSV_COL["brevo_company_id"]]),
        "crm_checked":            _str_or_none(csv_row[CSV_COL["brevo_company_id"]]) is not None,
        "qualification_checked":  True,
        "raw":                    csv_row,   # preserve full row for provenance
    }


def map_to_qualified(csv_row: dict, sourced_tam_id: int) -> dict:
    return {
        "sourced_tam_id":         sourced_tam_id,
        "domain":                 _norm_domain(csv_row[CSV_COL["domain"]]),
        "market":                 MARKET,
        "company_name":           _str_or_none(csv_row[CSV_COL["company_name"]]),
        "employee_range":         _str_or_none(csv_row[CSV_COL["employee_range"]]),
        "country":                COUNTRY,
        "brevo_company_id":       _str_or_none(csv_row[CSV_COL["brevo_company_id"]]),
        "esp_detected":           _str_or_none(csv_row[CSV_COL["esp_detected"]]),
        "esp_score":              _int_or_none(csv_row[CSV_COL["esp_score"]]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print counts + first 3 mapped rows without writing.")
    args = parser.parse_args()

    if not args.csv_path.exists():
        sys.exit(f"CSV not found: {args.csv_path}")

    with args.csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("CSV is empty")

    print(f"CSV rows                        : {len(rows):,}")
    deduped = dedupe_by_domain(rows)
    print(f"Unique domains (best per group) : {len(deduped):,}")

    # Split: only non-Excluded rows go into qualified_tam_v2
    to_qualified = [r for r in deduped if r.get(CSV_COL["routing_action"]) != "Exclude"]
    excluded     = [r for r in deduped if r.get(CSV_COL["routing_action"]) == "Exclude"]
    print(f"→ sourced_tam_v2   inserts      : {len(deduped):,}")
    print(f"→ qualified_tam_v2 inserts      : {len(to_qualified):,}  (excluded: {len(excluded):,})")

    if args.dry_run:
        print("\nSample sourced_tam_v2 payload (first 3):")
        for r in deduped[:3]:
            payload = map_to_sourced(r)
            payload["raw"] = "<full csv row omitted for readability>"
            print(json.dumps(payload, indent=2))
        print("\nSample qualified_tam_v2 payload (first 3):")
        for r in to_qualified[:3]:
            print(json.dumps(map_to_qualified(r, sourced_tam_id=-1), indent=2))
        return

    sb = get_supabase()

    # ── Insert sourced_tam_v2 in batches, capturing the returned ids ──────────
    sourced_id_by_domain: dict[str, int] = {}
    batch = 500
    inserted_src = 0
    for i in range(0, len(deduped), batch):
        chunk = [map_to_sourced(r) for r in deduped[i:i + batch]]
        resp = sb.table("sourced_tam_v2").upsert(
            chunk, on_conflict="domain,market,company_name"
        ).execute()
        for row in resp.data:
            sourced_id_by_domain[row["domain"]] = row["id"]
        inserted_src += len(chunk)
        print(f"  sourced_tam_v2: upserted {inserted_src:,}/{len(deduped):,}")

    # ── Insert qualified_tam_v2 rows with the captured sourced_tam_id ─────────
    inserted_qual = 0
    for i in range(0, len(to_qualified), batch):
        chunk_csv = to_qualified[i:i + batch]
        chunk = []
        for r in chunk_csv:
            d = _norm_domain(r[CSV_COL["domain"]])
            sid = sourced_id_by_domain.get(d)
            if sid is None:
                continue
            chunk.append(map_to_qualified(r, sourced_tam_id=sid))
        sb.table("qualified_tam_v2").upsert(
            chunk, on_conflict="domain,market,company_name"
        ).execute()
        inserted_qual += len(chunk)
        print(f"  qualified_tam_v2: upserted {inserted_qual:,}/{len(to_qualified):,}")

    print(f"\n✅ Done. sourced_tam_v2={inserted_src:,}  qualified_tam_v2={inserted_qual:,}")
    print("Next: POST /pipelines/enrich   →   Claude fills account_fit_score")
    print("      POST /pipelines/prioritize →  promote to priority_tam")


if __name__ == "__main__":
    main()
