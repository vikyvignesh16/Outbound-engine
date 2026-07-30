"""One-off import: DACH/FR/US Clay contact exports -> sourced_contacts.

Source files (data/Campaign Batches -1 /):
  US ABM Batch -2 - DACH.csv   (DE/AT/CH)
  US ABM Batch -2 - FR.csv     (FR)
  US ABM Batch -2 - US.csv     (US)

Unlike scripts/import_clay_contacts.py, these exports have no Market column
at all, and batch_number can't be hand-set as a constant since DACH/US share
one campaign_batches batch (see monthly_batch.py's per-group numbering) while
FR is a separate one. Both market and batch_number are resolved per-domain by
looking them up in campaign_batches instead.

Domains with no campaign_batches match are skipped (not pushed to Clay via
our pipeline, so we have no authoritative market/batch for them) — logged for
visibility rather than silently dropped.

Relevance score column name varies per file ("Brevo Relevance Score" /
"Relevance Score" / "Contact Relevance Score") but is always identical to
"Use AI Relevance Score" in every row (confirmed during the pre-import
assessment) - so this script reads the one universal column instead of
mapping three different names.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all  # noqa: E402
from utils.linkedin import normalise_linkedin_url  # noqa: E402

BASE = Path(__file__).resolve().parents[1] / "data" / "Campaign Batches -1 "
FILES = {
    "DACH": BASE / "US ABM Batch -2 - DACH.csv",
    "FR":   BASE / "US ABM Batch -2 - FR.csv",
    "US":   BASE / "US ABM Batch -2 - US.csv",
}
EMAIL_COL = {"DACH": "Email", "FR": "(Lusha) Work email", "US": "Email"}

# A domain can legitimately have campaign_batches rows under more than one
# market (confirmed real case: thebicestercollection.com has both a UKI row
# and a new FR row) — so lookups must be scoped to each file's own expected
# market set, not domain alone, or a company already contacted under a
# different market's batch gets misattributed.
EXPECTED_MARKETS = {"DACH": {"DE", "AT", "CH"}, "FR": {"FR"}, "US": {"US"}}


def _coerce_int(val):
    val = (val or "").strip()
    if not val:
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def map_row(row: dict, email_col: str) -> dict | None:
    domain = (row.get("Company Domain") or "").strip().lower()
    linkedin_url = normalise_linkedin_url(row.get("LinkedIn Profile"))
    if not domain or not linkedin_url:
        return None
    return {
        "domain":              domain,
        "linkedin_url":        linkedin_url,
        "company_name":        (row.get("Company Table Data") or "").strip() or None,
        "first_name":          (row.get("First Name") or "").strip() or None,
        "last_name":           (row.get("Last Name") or "").strip() or None,
        "job_title":           (row.get("Job Title") or "").strip() or None,
        "email":               (row.get(email_col) or "").strip() or None,
        "relevance_score":     _coerce_int(row.get("Use AI Relevance Score")),
        "relevance_reasoning": (row.get("Use AI Reasoning") or "").strip() or None,
        "raw": {
            "location":      (row.get("Location") or "").strip(),
            "confidence":    (row.get("Confidence") or "").strip(),
            "clay_full_row": row,
        },
    }


def main(dry_run: bool) -> None:
    cb_rows = fetch_all("campaign_batches", "domain, market, batch_number")
    cb_by_domain_market: dict[tuple[str, str], dict] = {
        (r["domain"], r["market"]): r for r in cb_rows
    }

    sb = get_supabase() if not dry_run else None

    totals = {"mapped": 0, "no_campaign_batch_match": 0, "skipped_no_domain_or_li": 0, "upserted": 0}
    unmatched_domains: set[str] = set()

    for label, path in FILES.items():
        expected_markets = EXPECTED_MARKETS[label]
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

        mapped_rows = []
        for row in rows:
            m = map_row(row, EMAIL_COL[label])
            if m is None:
                totals["skipped_no_domain_or_li"] += 1
                continue
            cb = next(
                (cb_by_domain_market[(m["domain"], mk)] for mk in expected_markets
                 if (m["domain"], mk) in cb_by_domain_market),
                None,
            )
            if not cb:
                totals["no_campaign_batch_match"] += 1
                unmatched_domains.add(m["domain"])
                continue
            m["market"] = cb["market"]
            m["batch_number"] = cb["batch_number"]
            m["source"] = "clay"
            mapped_rows.append(m)

        print(f"{label}: {len(rows)} rows -> {len(mapped_rows)} mappable")
        totals["mapped"] += len(mapped_rows)

        if dry_run:
            for m in mapped_rows[:2]:
                print("  sample:", {k: v for k, v in m.items() if k != "raw"})
            continue

        for i in range(0, len(mapped_rows), 100):
            chunk = mapped_rows[i:i + 100]
            sb.table("sourced_contacts").upsert(chunk, on_conflict="linkedin_url").execute()
            totals["upserted"] += len(chunk)

    print("\n--- Summary ---")
    print(f"Mapped (domain + linkedin_url present): {totals['mapped']}")
    print(f"Skipped (no domain or no linkedin_url):  {totals['skipped_no_domain_or_li']}")
    print(f"Skipped (no campaign_batches match):     {totals['no_campaign_batch_match']}")
    if unmatched_domains:
        print(f"  unmatched domains: {sorted(unmatched_domains)}")
    if not dry_run:
        print(f"Upserted into sourced_contacts:           {totals['upserted']}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
