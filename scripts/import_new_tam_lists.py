"""One-shot import of the new US/FR/UKI/DACH x {High Senders, Omnichannel} TAM
lists (data/TAM/*.csv) into sourced_tam_v2.

Matching key is (domain, market, company_name) — the real unique constraint
added by migration 009 specifically to allow the same domain to appear more
than once across distinct entities (acquisitions, franchises, subsidiary
brands, e.g. multiple MDPI journals all on mdpi.com).

For each CSV row:
  - If (domain, market, company_name) already exists in sourced_tam_v2 ->
    UPDATE only tam_segment (comma-joins segments if the company appears in
    both a High Senders and an Omnichannel file for the same market). No new
    row, no duplicate.
  - Otherwise -> INSERT a new row with crm_checked=False, qualification_checked=False
    so it flows into the existing Step 2-4 pipeline (run_crm_check ->
    run_qualification_rules -> run_technographic).

Usage:
    source .env && python scripts/import_new_tam_lists.py --dry-run
    source .env && python scripts/import_new_tam_lists.py
"""
import argparse
import csv
import logging
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

TAM_DIR = Path(__file__).resolve().parents[1] / "data" / "TAM"

COUNTRY_TO_MARKET = {
    "Germany": "DE", "Switzerland": "CH", "Austria": "AT",
    "France": "FR",
    "United Kingdom of Great Britain and Northern Ireland": "UK",
    "Ireland": "Ireland",
    "United States": "US",
}

FILES = [
    ("DACH_High_senders.csv", "High Senders"),
    ("DACH_Omnichannel.csv", "Omnichannel"),
    ("France_High_senders.csv", "High Senders"),
    ("France_Omnichannel.csv", "Omnichannel"),
    ("UKI_High_senders.csv", "High Senders"),
    ("UKI_Omnichannle.csv", "Omnichannel"),
    ("US_High_senders.csv", "High Senders"),
    ("US_Omnichannel.csv", "Omnichannel"),
]


def load_csv_rows() -> dict:
    """Returns {(domain, market, company_name): {"segments": set(), "row": <csv row dict>}}."""
    merged = {}
    for fname, segment in FILES:
        path = TAM_DIR / fname
        with path.open(encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            n = 0
            for row in reader:
                domain = (row.get("Domain") or "").strip().lower()
                name = (row.get("Name") or "").strip()
                country = (row.get("Country") or "").strip()
                market = COUNTRY_TO_MARKET.get(country)
                if not domain or not name or not market:
                    continue
                key = (domain, market, name)
                if key not in merged:
                    merged[key] = {"segments": set(), "row": row, "market": market}
                merged[key]["segments"].add(segment)
                n += 1
        logger.info("loaded %s: %d usable rows", fname, n)
    return merged


def build_insert_payload(key: tuple, entry: dict) -> dict:
    domain, market, name = key
    row = entry["row"]
    segments = ",".join(sorted(entry["segments"]))
    return {
        "domain":                domain,
        "market":                market,
        "company_name":          name,
        "company_type":          (row.get("Type") or "").strip() or None,
        "employee_range":        (row.get("Size") or "").strip() or None,
        "location":              (row.get("Location") or "").strip() or None,
        "country":               (row.get("Country") or "").strip() or None,
        "linkedin_url":          (row.get("LinkedIn URL") or "").strip() or None,
        "vertical":              (row.get("Primary Industry") or "").strip() or None,
        "tam_segment":           segments,
        "raw":                   dict(row),
        "crm_checked":           False,
        "qualification_checked": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Report counts only, no writes")
    args = parser.parse_args()

    sb = get_supabase()

    logger.info("loading CSVs from %s", TAM_DIR)
    merged = load_csv_rows()
    logger.info("total unique (domain, market, company_name) rows across all files: %d", len(merged))

    logger.info("fetching existing sourced_tam_v2 rows per market for dedup...")
    existing_by_market = {}
    markets = set(m for (_, m, _) in merged)
    for m in markets:
        rows = fetch_all("sourced_tam_v2", "id, domain, company_name, tam_segment", [("eq", "market", m)])
        existing_by_market[m] = {
            (r["domain"].strip().lower(), (r["company_name"] or "").strip()): r
            for r in rows
        }
        logger.info("  %s: %d existing rows fetched", m, len(rows))

    to_insert = []
    to_update = []  # (existing_row_dict, new_segments_str)

    for key, entry in merged.items():
        domain, market, name = key
        existing_row = existing_by_market.get(market, {}).get((domain, name))
        if existing_row:
            current_segments = set((existing_row.get("tam_segment") or "").split(",")) - {""}
            merged_segments = current_segments | entry["segments"]
            merged_str = ",".join(sorted(merged_segments))
            if merged_str != (existing_row.get("tam_segment") or ""):
                to_update.append((existing_row, merged_str))
        else:
            to_insert.append(build_insert_payload(key, entry))

    logger.info("plan: %d new rows to insert, %d existing rows to tag with tam_segment", len(to_insert), len(to_update))

    if args.dry_run:
        by_market = defaultdict(int)
        for r in to_insert:
            by_market[r["market"]] += 1
        logger.info("net-new by market: %s", dict(by_market))
        logger.info("DRY RUN — no writes performed")
        return

    logger.info("inserting %d new rows into sourced_tam_v2...", len(to_insert))
    for i in range(0, len(to_insert), 500):
        chunk = to_insert[i:i + 500]
        sb.table("sourced_tam_v2").insert(chunk).execute()
        logger.info("  inserted %d/%d", min(i + 500, len(to_insert)), len(to_insert))

    logger.info("updating tam_segment on %d existing rows...", len(to_update))
    for existing_row, segments_str in to_update:
        sb.table("sourced_tam_v2").update({"tam_segment": segments_str}).eq("id", existing_row["id"]).execute()

    logger.info("done. inserted=%d updated=%d", len(to_insert), len(to_update))


if __name__ == "__main__":
    main()
