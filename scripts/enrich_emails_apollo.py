"""Enrich missing emails via Apollo's Bulk People Enrichment endpoint.

Second-pass complement to enrich_emails_lusha.py — targets rows that:
  - are in batch #2 (or --batch argument)
  - still have NULL/empty email
  - have at least a linkedin_url OR (first_name + last_name + domain)

Endpoint: POST https://api.apollo.io/api/v1/people/bulk_match
Auth:     X-Api-Key header
Batch:    up to 10 per request (Apollo cap)

Waterfall enabled — run_waterfall_email=true tells Apollo to lean on its
secondary sources when the primary DB doesn't have a work email cached.
This is why we run Apollo AFTER Lusha: cheaper waterfall spend, higher hit
rate on the residual.

Response matching is by ORDINAL POSITION. Apollo's `matches` array is in
the exact order of the `details` we sent, with `null` for not-found rows.
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values
os.environ.update({k: v for k, v in dotenv_values('.env').items() if v})

import httpx
from db.client import get_supabase

APOLLO_URL  = "https://api.apollo.io/api/v1/people/bulk_match"
API_KEY     = os.environ["APOLLO_API_KEY"]
BATCH_LIMIT = 10  # Apollo hard cap
OUT_CSV     = Path("data/batch2_apollo_email_delta.csv")


def build_details(contacts: list[dict]) -> list[dict]:
    """One detail per contact. Prefer linkedin_url (Apollo accepts the
    obfuscated Sales Nav form too, unlike Lusha). Fallback: name + domain."""
    details = []
    for c in contacts:
        li = (c.get("linkedin_url") or "").strip()
        if li:
            details.append({"linkedin_url": li})
            continue
        details.append({
            "first_name": c.get("first_name") or "",
            "last_name":  c.get("last_name") or "",
            "domain":     c.get("domain") or "",
        })
    return details


def call_apollo(details: list[dict]) -> dict:
    body = {
        "details":                details,
        "reveal_personal_emails": True,
        # run_waterfall_email would give higher hit rate, but Apollo requires
        # a webhook_url for waterfall (email is returned async). For a one-shot
        # sweep on this residual we stay synchronous and accept lower coverage.
    }
    resp = httpx.post(
        APOLLO_URL,
        headers={
            "Content-Type":  "application/json",
            "Cache-Control": "no-cache",
            "accept":        "application/json",
            "X-Api-Key":     API_KEY,
        },
        json=body,
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
    return resp.json()


def extract_email(match: dict | None) -> tuple[str | None, str | None]:
    """Prefer verified `email` field, fall back to `personal_emails[0]`."""
    if not match:
        return None, None
    email = (match.get("email") or "").strip()
    status = match.get("email_status") or ""
    if email:
        return email, status
    p = match.get("personal_emails") or []
    if p and p[0]:
        return p[0].strip(), (status or "personal")
    return None, None


def main() -> None:
    sb = get_supabase()
    rows = sb.table("sourced_contacts").select(
        "id,domain,company_name,first_name,last_name,linkedin_url,email,source"
    ).eq("batch_number", 2).execute().data
    rows = [r for r in rows if not (r.get("email") or "").strip()]
    print(f"contacts still missing email (post-Lusha): {len(rows)}")

    findings: list[dict] = []
    hits = 0

    for i in range(0, len(rows), BATCH_LIMIT):
        chunk   = rows[i:i + BATCH_LIMIT]
        details = build_details(chunk)
        print(f"\n▶ Apollo batch {i//BATCH_LIMIT + 1}: {len(details)} contacts")
        try:
            data = call_apollo(details)
        except httpx.HTTPStatusError:
            break

        if i == 0:
            print(f"  response top-level keys: {list(data.keys())}")
            first_match = next((m for m in (data.get('matches') or []) if m), None)
            if first_match:
                relevant = {k: first_match.get(k) for k in [
                    "first_name","last_name","email","email_status",
                    "personal_emails","linkedin_url"
                ]}
                print(f"  sample match: {json.dumps(relevant, indent=2)}")

        matches = data.get("matches") or []
        if len(matches) != len(chunk):
            print(f"  ⚠️  {len(matches)} matches vs {len(chunk)} inputs — ordinal may be off")

        for idx, c in enumerate(chunk):
            m = matches[idx] if idx < len(matches) else None
            email, status = extract_email(m)
            findings.append({
                "contact_id":       c["id"],
                "first_name":       c["first_name"],
                "last_name":        c["last_name"],
                "company_name":     c["company_name"],
                "domain":           c["domain"],
                "source":           c["source"],
                "linkedin_url":     c["linkedin_url"],
                "email_found":      email or "",
                "email_status":     status or "",
                "apollo_matched":   bool(m),
            })
            if email:
                sb.table("sourced_contacts").update({"email": email}).eq("id", c["id"]).execute()
                hits += 1

        # be nice to Apollo — small pause between batches
        time.sleep(0.5)

    # Write delta CSV
    OUT_CSV.parent.mkdir(exist_ok=True, parents=True)
    if findings:
        with OUT_CSV.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            for row in findings:
                w.writerow(row)

    print("\n" + "=" * 60)
    print(f"Total contacts checked:  {len(findings)}")
    print(f"Emails found + written:  {hits}  ({hits/len(findings)*100:.0f}% of pool)")
    print(f"Still missing:           {len(findings) - hits}")
    print(f"Delta CSV:               {OUT_CSV}")


if __name__ == "__main__":
    main()
