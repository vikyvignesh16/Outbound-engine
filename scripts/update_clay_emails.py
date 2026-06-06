"""Update emails on existing sourced_contacts rows from a manual enrichment CSV.

Use case: the in-app email enrichment API is broken, so emails for the Clay-sourced
contacts already in sourced_contacts (153 rows missing emails for batch 1) have
been enriched manually outside the system. This script joins the enrichment CSV
back to sourced_contacts on linkedin_url and writes the email + email_provider.

Policy (per user instruction): latest enrichment wins — every match overwrites
the existing email and email_provider even if a value was already there.

Required CSV columns:
    linkedin_url
    email
    email_provider

Anything else is ignored. Rows with blank linkedin_url or blank email are
skipped with a count.

Usage:
    python scripts/update_clay_emails.py data/<your_enrichment_file>.csv --dry-run
    python scripts/update_clay_emails.py data/<your_enrichment_file>.csv
    python scripts/update_clay_emails.py data/<your_enrichment_file>.csv --batch-number 1
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase  # noqa: E402


def normalise_url(url: str) -> str:
    """Strip trailing slashes + lowercase the path; LinkedIn URLs are
    case-insensitive on the path so a literal equality check would
    miss valid matches otherwise."""
    u = (url or "").strip()
    if not u:
        return ""
    # Drop any trailing slash and lower-case for matching only.
    return u.rstrip("/").lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--batch-number", type=int, default=None,
                        help="Restrict updates to this batch_number (extra safety).")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.csv_path.exists():
        sys.exit(f"CSV not found: {args.csv_path}")

    # Parse CSV
    enrichments: list[dict] = []
    skipped_blank = 0
    with args.csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        for col in ("linkedin_url", "email", "email_provider"):
            if col not in cols:
                sys.exit(f"CSV missing required column '{col}'. Got: {cols}")

        for row in reader:
            li = normalise_url(row.get("linkedin_url") or "")
            email = (row.get("email") or "").strip()
            provider = (row.get("email_provider") or "").strip() or None
            if not li or not email:
                skipped_blank += 1
                continue
            enrichments.append({
                "linkedin_url_norm": li,
                "email":             email,
                "email_provider":    provider,
            })

    print(f"Loaded {len(enrichments)} enrichment rows from {args.csv_path}")
    print(f"  skipped (blank linkedin_url or email): {skipped_blank}")

    if not enrichments:
        return

    sb = get_supabase()

    # Pull every candidate sourced_contacts row in one shot (much faster than
    # per-row lookups). Filter by batch_number if provided for safety.
    q = sb.table("sourced_contacts").select(
        "id,domain,linkedin_url,email,email_provider,source,batch_number"
    )
    if args.batch_number is not None:
        q = q.eq("batch_number", args.batch_number)
    q = q.not_.is_("linkedin_url", "null")

    # Paginate over the result (Supabase default limit is 1000)
    all_sc: list[dict] = []
    page = 0
    PAGE = 1000
    while True:
        chunk = q.range(page * PAGE, (page + 1) * PAGE - 1).execute().data
        if not chunk:
            break
        all_sc.extend(chunk)
        if len(chunk) < PAGE:
            break
        page += 1
    print(f"  loaded {len(all_sc)} sourced_contacts rows with linkedin_url"
          + (f" (batch_number={args.batch_number})" if args.batch_number is not None else ""))

    # Index sourced_contacts by normalised linkedin_url
    by_url: dict[str, dict] = {}
    for r in all_sc:
        by_url[normalise_url(r["linkedin_url"])] = r

    # Match
    matched: list[tuple[dict, dict]] = []     # (sc_row, enrichment)
    unmatched: list[dict] = []                # enrichment rows with no SC match
    for e in enrichments:
        sc = by_url.get(e["linkedin_url_norm"])
        if sc:
            matched.append((sc, e))
        else:
            unmatched.append(e)

    print(f"  matched:   {len(matched)}")
    print(f"  unmatched: {len(unmatched)}"
          + ("" if not unmatched else f"  → e.g. {unmatched[0]['linkedin_url_norm']}"))

    # Categorise matches by what will change
    will_fill_blank = 0
    will_overwrite = 0
    no_change = 0
    for sc, e in matched:
        old_email = (sc.get("email") or "").strip()
        if not old_email:
            will_fill_blank += 1
        elif old_email.lower() != e["email"].lower():
            will_overwrite += 1
        else:
            no_change += 1
    print(f"  → fill blank: {will_fill_blank}   overwrite: {will_overwrite}   "
          f"unchanged: {no_change}")

    if args.dry_run:
        print("\nDry-run: nothing written. First 5 overwrites:")
        n = 0
        for sc, e in matched:
            old = sc.get("email") or ""
            if old and old.lower() != e["email"].lower():
                print(f"  {sc['domain']:35s}  {old}  →  {e['email']}  ({e['email_provider']})")
                n += 1
                if n >= 5:
                    break
        return

    # ── Writes ────────────────────────────────────────────────────────────────
    updated = 0
    for sc, e in matched:
        sb.table("sourced_contacts").update({
            "email":          e["email"],
            "email_provider": e["email_provider"],
        }).eq("id", sc["id"]).execute()
        updated += 1

    print(f"\n✅ Update complete:")
    print(f"  sourced_contacts updated: {updated}")
    if unmatched:
        print(f"  ⚠️  unmatched enrichment rows: {len(unmatched)}")
        print(f"      (linkedin_urls from your CSV that have no matching sourced_contacts row)")


if __name__ == "__main__":
    main()
