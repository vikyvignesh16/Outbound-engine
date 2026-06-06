"""Promote user-reviewed phantombuster_contacts to sourced_contacts.

Reads the CSV exported by the score_contacts preview step, where the user
has:
  - Set `keep` to 'yes' or 'no' per row
  - Added `email` and `email_provider` columns after running manual enrichment

For each row where keep=='yes' AND email is non-blank, the script:
  1. Looks up the phantombuster_contacts row by id (preserves company_name,
     market, batch_number, etc).
  2. Upserts into sourced_contacts with source='linkedin', plus the email
     + email_provider from the CSV (NOT what's in phantombuster_contacts —
     PB output has no email).
  3. Respects Clay precedence: skips upsert if a row with the same normalised
     linkedin_url already exists with source='clay'.

Every row that was reviewed (kept OR excluded OR no-email) is flagged
promoted_to_sourced_contacts=true on phantombuster_contacts so they drop
out of future preview/promote calls — even ones we couldn't promote get
marked so the preview list doesn't keep showing the same dead-ends.

Usage:
    python scripts/promote_reviewed_contacts.py data/batch1_qualified_for_review.csv --dry-run
    python scripts/promote_reviewed_contacts.py data/batch1_qualified_for_review.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all  # noqa: E402


def normalise_linkedin_url(url: str) -> str:
    """Canonicalise a LinkedIn URL for cross-source dedup against Clay.

    Lowercases, drops https?:// + www. + trailing slash + query/fragment.
    e.g. "https://www.linkedin.com/in/Foo/" → "linkedin.com/in/foo"
    """
    u = (url or "").strip().lower()
    if not u:
        return ""
    for prefix in ("https://", "http://"):
        if u.startswith(prefix):
            u = u[len(prefix):]
            break
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/").split("?", 1)[0].split("#", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.csv_path.exists():
        sys.exit(f"CSV not found: {args.csv_path}")

    # All keep=yes rows go to sourced_contacts. LinkedIn URL is the unique key,
    # so emailless contacts are still valuable: we can target them via LinkedIn
    # campaigns now, and backfill email later when enrichment catches up.
    to_promote: dict[str, dict] = {}   # pbc_id -> {email, email_provider} (both may be None)
    excluded: list[str] = []

    with args.csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        # Match required columns case- and space-insensitively so manually-
        # exported CSVs with "Email" / "Email Provider" work alongside the
        # pipeline's lowercase + underscore originals.
        def _norm(s: str) -> str:
            return s.strip().lower().replace(" ", "_")
        col_lookup = {_norm(c): c for c in cols}

        def find(name: str) -> str | None:
            return col_lookup.get(_norm(name))

        col_pbc      = find("pbc_id")
        col_keep     = find("keep")
        col_email    = find("email")
        col_provider = find("email_provider")
        for required, col in (("pbc_id", col_pbc), ("email", col_email),
                              ("email_provider", col_provider)):
            if col is None:
                sys.exit(f"CSV missing required column '{required}'. Got: {cols}")

        for row in reader:
            pbc_id = (row.get(col_pbc) or "").strip()
            if not pbc_id:
                continue
            keep_val = ((row.get(col_keep) or "") if col_keep else "").strip().lower()
            email = (row.get(col_email) or "").strip()
            provider = (row.get(col_provider) or "").strip() or None

            if keep_val not in ("yes", "y", "true", "1"):
                excluded.append(pbc_id)
                continue
            to_promote[pbc_id] = {
                "email":          email or None,
                "email_provider": provider,
            }

    with_email_count = sum(1 for v in to_promote.values() if v["email"])
    no_email_count = len(to_promote) - with_email_count
    print(f"Reviewed CSV: {args.csv_path}")
    print(f"  keep=yes + email present: {with_email_count}  → will promote with email")
    print(f"  keep=yes + no email:      {no_email_count}  → will promote (linkedin_url only, email NULL)")
    print(f"  keep=no/excluded:         {len(excluded)}  → marked promoted, not sent")

    if not to_promote and not excluded:
        print("Nothing to do.")
        return

    sb = get_supabase()

    # Pull the full PB rows for the ones we'll actually write
    rows: list[dict] = []
    if to_promote:
        ids = list(to_promote.keys())
        rows = fetch_all(
            "phantombuster_contacts",
            "id,domain,company_name,market,batch_number,first_name,last_name,"
            "job_title,linkedin_url,relevance_score,seniority_score,"
            "relevance_reasoning,raw",
            filters=[("in_", "id", ids)],
        )
        print(f"  fetched {len(rows)} PB rows for promotion")
        if len(rows) < len(ids):
            missing = set(ids) - {r["id"] for r in rows}
            print(f"  ⚠️  {len(missing)} pbc_ids not found in DB (CSV may be stale): "
                  f"{list(missing)[:3]}{'…' if len(missing) > 3 else ''}")

    if args.dry_run:
        print("\nDry-run: not writing. Sample of first 5 to be promoted:")
        for r in rows[:5]:
            enrich = to_promote[r["id"]]
            email_display = enrich["email"] or "(no email)"
            print(f"  {r['domain']:35s}  r={r['relevance_score']} s={r['seniority_score']}  "
                  f"{(r.get('job_title') or '')[:40]:40s}  → {email_display}  ({enrich['email_provider']})")
        return

    # ── Writes ────────────────────────────────────────────────────────────────
    promoted = 0
    skipped_clay = 0
    skipped_no_li = 0
    for r in rows:
        enrich = to_promote[r["id"]]
        email = enrich["email"]
        provider = enrich["email_provider"]

        li_norm = normalise_linkedin_url(r.get("linkedin_url") or "")
        if not li_norm:
            skipped_no_li += 1
            continue

        # Clay precedence: if a row with the same normalised linkedin_url
        # already exists with source='clay', skip (PB never overwrites Clay).
        existing = sb.table("sourced_contacts").select("id,source").eq(
            "linkedin_url", li_norm
        ).limit(1).execute().data
        if existing and existing[0].get("source") == "clay":
            skipped_clay += 1
            continue

        sourced_row = {
            "domain":              r["domain"],
            "company_name":        r["company_name"],
            "market":              r["market"],
            "batch_number":        r["batch_number"],
            "source":              "linkedin",
            "email":               email,
            "email_provider":      provider,
            "first_name":          r.get("first_name"),
            "last_name":           r.get("last_name"),
            "job_title":           r.get("job_title"),
            "linkedin_url":        li_norm,
            "relevance_score":     r.get("relevance_score"),
            "seniority_score":     r.get("seniority_score"),
            "relevance_reasoning": r.get("relevance_reasoning"),
            "raw":                 r.get("raw"),
        }
        sb.table("sourced_contacts").upsert(
            sourced_row, on_conflict="linkedin_url"
        ).execute()
        promoted += 1

    # Mark every reviewed pbc row as promoted so they drop out of future previews.
    all_reviewed = list(to_promote.keys()) + excluded
    if all_reviewed:
        CHUNK = 200
        for i in range(0, len(all_reviewed), CHUNK):
            sb.table("phantombuster_contacts").update({
                "promoted_to_sourced_contacts": True,
            }).in_("id", all_reviewed[i:i+CHUNK]).execute()

    print(f"\n✅ Promotion complete:")
    print(f"  promoted to sourced_contacts: {promoted}")
    print(f"  skipped (Clay precedence):    {skipped_clay}")
    print(f"  skipped (no LinkedIn URL):    {skipped_no_li}")
    print(f"  pbc rows flagged promoted:    {len(all_reviewed)}")


if __name__ == "__main__":
    main()
