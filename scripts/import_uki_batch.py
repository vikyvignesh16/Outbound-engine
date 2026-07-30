"""One-off import: UKI Clay contact export -> sourced_contacts.

Source file (data/Campaign Batches -1 /):
  US ABM Batch -2 - UKI (1).csv   (UK/Ireland)

Same shape and resolution approach as scripts/import_dach_fr_us_batch1.py
(no Market column in the export; market + batch_number resolved per-domain
via campaign_batches), with one addition: 11 domains in this file didn't
match campaign_batches directly, but all 11 turned out to be the same
companies recorded under a different domain spelling there (mostly a
careers-subdomain vs. main-domain mismatch, e.g. burberry.com in this CSV
vs. burberrycareers.com in campaign_batches/priority_tam). Confirmed via a
1:1 company_name match before writing this script — not guessed.

For those company-name-fallback matches, the row is written using
CAMPAIGN_BATCHES' domain, not the CSV's domain — content.py's sequence
generation joins sourced_contacts to priority_tam by domain, and that
enrichment data (vertical, ESP, archetype, etc.) lives under the
campaign_batches/priority_tam domain. Using the CSV's own domain instead
would leave these contacts unable to find their company context. The
original CSV domain is preserved in raw.clay_domain for traceability.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all  # noqa: E402
from utils.linkedin import normalise_linkedin_url  # noqa: E402

PATH = Path(__file__).resolve().parents[1] / "data" / "Campaign Batches -1 " / "US ABM Batch -2 - UKI (1).csv"
EMAIL_COL = "Email"
EXPECTED_MARKETS = {"UK", "Ireland"}

# Confirmed 1:1 by company_name match against campaign_batches before this
# import — see module docstring. CSV domain -> real campaign_batches domain.
DOMAIN_OVERRIDES: dict[str, str] = {
    "burberry.com":                     "burberrycareers.com",
    "mcarthurglen.com":                 "mcarthurglengroup.com",
    "stonegatecareers.co.uk":           "stonegategroup.co.uk",
    "tescoireland.ie":                  "tesco.ie",
    "iconichotelsresorts.com":          "iconicluxuryhotels.com",
    "poltronesofa.co.uk":               "scs.co.uk",
    "theaspireway.com":                 "aspirelounges.com",
    "brownthomasarnottscareers.com":    "arnotts.ie",
    "estate-escapes.co.uk":             "devonshirehotels.co.uk",
    "louisfitzgerald.com":              "louisfitzgerald.ie",
    "thelandmarkhotel.com":             "workingfrom.com",
}


def _coerce_int(val):
    val = (val or "").strip()
    if not val:
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def map_row(row: dict) -> dict | None:
    csv_domain = (row.get("Company Domain") or "").strip().lower()
    linkedin_url = normalise_linkedin_url(row.get("LinkedIn Profile"))
    if not csv_domain or not linkedin_url:
        return None
    resolved_domain = DOMAIN_OVERRIDES.get(csv_domain, csv_domain)
    return {
        "domain":              resolved_domain,
        "linkedin_url":        linkedin_url,
        "company_name":        (row.get("Company Table Data") or "").strip() or None,
        "first_name":          (row.get("First Name") or "").strip() or None,
        "last_name":           (row.get("Last Name") or "").strip() or None,
        "job_title":           (row.get("Job Title") or "").strip() or None,
        "email":               (row.get(EMAIL_COL) or "").strip() or None,
        "relevance_score":     _coerce_int(row.get("Use AI Relevance Score")),
        "relevance_reasoning": (row.get("Use AI Reasoning") or "").strip() or None,
        "raw": {
            "location":      (row.get("Location") or "").strip(),
            "confidence":    (row.get("Confidence") or "").strip(),
            "clay_domain":   csv_domain,
            "clay_full_row": row,
        },
    }


def main(dry_run: bool) -> None:
    cb_rows = fetch_all("campaign_batches", "domain, market, batch_number")
    cb_by_domain_market: dict[tuple[str, str], dict] = {
        (r["domain"], r["market"]): r for r in cb_rows
    }

    sb = get_supabase() if not dry_run else None

    with PATH.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    mapped_rows = []
    skipped_no_domain_or_li = 0
    no_match = set()

    for row in rows:
        m = map_row(row)
        if m is None:
            skipped_no_domain_or_li += 1
            continue
        cb = next(
            (cb_by_domain_market[(m["domain"], mk)] for mk in EXPECTED_MARKETS
             if (m["domain"], mk) in cb_by_domain_market),
            None,
        )
        if not cb:
            no_match.add(m["domain"])
            continue
        m["market"] = cb["market"]
        m["batch_number"] = cb["batch_number"]
        m["source"] = "clay"
        mapped_rows.append(m)

    print(f"UKI: {len(rows)} rows -> {len(mapped_rows)} mappable")

    if dry_run:
        for m in mapped_rows[:3]:
            print("  sample:", {k: v for k, v in m.items() if k != "raw"})
    else:
        upserted = 0
        for i in range(0, len(mapped_rows), 100):
            chunk = mapped_rows[i:i + 100]
            sb.table("sourced_contacts").upsert(chunk, on_conflict="linkedin_url").execute()
            upserted += len(chunk)
        print(f"Upserted into sourced_contacts: {upserted}")

    print("\n--- Summary ---")
    print(f"Skipped (no domain or no linkedin_url): {skipped_no_domain_or_li}")
    print(f"Skipped (no campaign_batches match, incl. overrides): {len(no_match)}")
    if no_match:
        print(f"  still-unmatched domains: {sorted(no_match)}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
