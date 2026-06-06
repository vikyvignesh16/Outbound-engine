"""Ingest a manually-run PhantomBuster Sales Nav Search Export CSV into
phantombuster_contacts, and reconcile the corresponding contact_gaps rows.

Why this exists: the in-pipeline PB Sales Nav agent was returning 0 contacts for
~130 companies launched in batched (spreadsheetUrl) mode, because PB doesn't
honour numberOfLinesPerLaunch for the Sales Nav agent. We exported the queued
sales_nav_url list, ran them by hand outside the pipeline, and now need to
load the results back in.

Attribution:
  PB row → companyId (a LinkedIn organization id, integer) → contact_gaps row
  via the `linkedin_company_id` column. The pipeline set linkedin_company_id
  on each gap row when Phase 1 completed.

Fallback for rows where the companyId field is blank: parse the URN
`urn:li:organization:<id>` out of the row's `query` field.

For "No results found" rows we mark the gap as no_contacts_found and write
nothing to phantombuster_contacts.

Usage:
    python scripts/ingest_manual_pb_csv.py data/Batch_1_Manual_v2.csv --batch-number 1 --dry-run
    python scripts/ingest_manual_pb_csv.py data/Batch_1_Manual_v2.csv --batch-number 1
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Make repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all  # noqa: E402


URN_RE = re.compile(r"urn%3Ali%3Aorganization%3A(\d+)")


def extract_company_id(row: dict) -> str | None:
    """Prefer the explicit companyId field; fall back to parsing the URN out of
    the `query` field for rows where PB left companyId blank."""
    cid = (row.get("companyId") or "").strip()
    if cid:
        return cid
    q = row.get("query") or ""
    m = URN_RE.search(q)
    return m.group(1) if m else None


def load_gap_index(batch_number: int) -> dict[str, dict]:
    """Map linkedin_company_id -> contact_gaps row for the given batch."""
    rows = fetch_all(
        "contact_gaps",
        "id,domain,company_name,market,batch_number,linkedin_company_id,phantombuster_status",
        filters=[("eq", "batch_number", batch_number)],
    )
    index: dict[str, dict] = {}
    for r in rows:
        cid = (r.get("linkedin_company_id") or "").strip()
        if cid:
            # Some rows had comma-joined ids ("2802,599552") — index each separately.
            for piece in cid.split(","):
                piece = piece.strip()
                if piece:
                    index[piece] = r
    return index


def pick_linkedin_url(row: dict) -> str | None:
    """Use the clean public LinkedIn URL when available; PB's `linkedInProfileUrl`
    is the Sales Nav internal obfuscated form (linkedin.com/in/ACw...), which
    isn't useful for Lemlist routing."""
    url = (row.get("defaultProfileUrl") or "").strip()
    if url:
        if not url.startswith("http"):
            url = "https://" + url.lstrip("/")
        return url
    fallback = (row.get("linkedInProfileUrl") or "").strip()
    return fallback or None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--batch-number", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and summarise only; write nothing to Supabase.")
    args = parser.parse_args()

    if not args.csv_path.exists():
        sys.exit(f"CSV not found: {args.csv_path}")

    print(f"Loading contact_gaps for batch {args.batch_number}…")
    gap_index = load_gap_index(args.batch_number)
    print(f"  indexed {len(gap_index)} linkedin_company_id entries")

    contacts_by_cid: dict[str, list[dict]] = defaultdict(list)
    no_results_cids: set[str] = set()
    unmatched_cids: set[str] = set()
    skipped_rows = 0

    with args.csv_path.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = extract_company_id(row)
            if not cid:
                skipped_rows += 1
                continue

            if (row.get("error") or "").strip() == "No results found":
                no_results_cids.add(cid)
                continue

            # Must have at least a profile URL to be useful
            li_url = pick_linkedin_url(row)
            if not li_url:
                skipped_rows += 1
                continue

            contacts_by_cid[cid].append({
                "first_name":   (row.get("firstName") or "").strip() or None,
                "last_name":    (row.get("lastName") or "").strip() or None,
                "job_title":    (row.get("title") or "").strip() or None,
                "linkedin_url": li_url,
                "raw":          {k: v for k, v in row.items() if v},
            })

    print(f"Parsed:")
    print(f"  contacts grouped under {len(contacts_by_cid)} companies, "
          f"{sum(len(v) for v in contacts_by_cid.values())} total rows")
    print(f"  no-results companies: {len(no_results_cids)}")
    print(f"  rows skipped (no companyId/no profile URL): {skipped_rows}")

    # Resolve which gap rows the data attaches to
    matched_for_contacts: dict[str, dict] = {}
    for cid in contacts_by_cid:
        gap = gap_index.get(cid)
        if gap:
            matched_for_contacts[cid] = gap
        else:
            unmatched_cids.add(cid)

    matched_for_noresults: dict[str, dict] = {}
    for cid in no_results_cids:
        gap = gap_index.get(cid)
        if gap:
            matched_for_noresults[cid] = gap
        else:
            unmatched_cids.add(cid)

    print(f"Resolved to gap rows:")
    print(f"  companies with contacts → matched gap: {len(matched_for_contacts)}")
    print(f"  no-results              → matched gap: {len(matched_for_noresults)}")
    if unmatched_cids:
        print(f"  ⚠️  unmatched companyId (no gap row): {len(unmatched_cids)} → "
              f"{sorted(unmatched_cids)[:5]}{'…' if len(unmatched_cids) > 5 else ''}")

    if args.dry_run:
        print("\nDry-run: showing first 3 matched companies and their counts:")
        for cid in list(matched_for_contacts.keys())[:3]:
            gap = matched_for_contacts[cid]
            print(f"  cid={cid}  domain={gap['domain']}  contacts={len(contacts_by_cid[cid])}")
        return

    # ── Writes ────────────────────────────────────────────────────────────────
    sb = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()
    contacts_inserted = 0
    contacts_skipped_dupes = 0
    gaps_marked_completed = 0
    gaps_marked_no_contacts = 0

    for cid, gap in matched_for_contacts.items():
        contact_rows = contacts_by_cid[cid]
        if not contact_rows:
            continue
        payload = []
        for c in contact_rows:
            payload.append({
                "batch_number":  gap["batch_number"],
                "domain":        gap["domain"],
                "company_name": gap.get("company_name"),
                "market":        gap.get("market"),
                "first_name":    c["first_name"],
                "last_name":     c["last_name"],
                "job_title":     c["job_title"],
                "linkedin_url":  c["linkedin_url"],
                "email":         None,
                "raw":           c["raw"],
            })
        # Upsert on the unique key (domain, linkedin_url, batch_number) so re-runs
        # don't double-write the same contact.
        try:
            res = sb.table("phantombuster_contacts").upsert(
                payload,
                on_conflict="domain,linkedin_url,batch_number",
                ignore_duplicates=False,
            ).execute()
            inserted = len(res.data or [])
            contacts_inserted += inserted
            if inserted < len(payload):
                contacts_skipped_dupes += (len(payload) - inserted)
        except Exception as exc:
            print(f"  ❌ upsert failed for cid={cid}: {exc}")
            continue

        sb.table("contact_gaps").update({
            "phantombuster_status": "completed",
            "contacts_found":       len(payload),
            "completed_at":         now_iso,
        }).eq("id", gap["id"]).execute()
        gaps_marked_completed += 1

    for cid, gap in matched_for_noresults.items():
        # If contacts also came through for this cid (rare), the completed branch
        # above already handled it — don't downgrade to no_contacts_found.
        if cid in matched_for_contacts:
            continue
        sb.table("contact_gaps").update({
            "phantombuster_status": "no_contacts_found",
            "contacts_found":       0,
            "completed_at":         now_iso,
        }).eq("id", gap["id"]).execute()
        gaps_marked_no_contacts += 1

    print(f"\n✅ Writes complete:")
    print(f"  phantombuster_contacts inserted: {contacts_inserted}")
    print(f"  phantombuster_contacts dupes:    {contacts_skipped_dupes}")
    print(f"  contact_gaps → completed:        {gaps_marked_completed}")
    print(f"  contact_gaps → no_contacts_found:{gaps_marked_no_contacts}")
    if unmatched_cids:
        print(f"  ⚠️  unmatched cids skipped: {len(unmatched_cids)}")
        print(f"      → run `python scripts/ingest_manual_pb_csv.py {args.csv_path} "
              f"--batch-number {args.batch_number} --dry-run` to inspect")


if __name__ == "__main__":
    main()
