"""Enrich missing emails on batch #2 contacts via Lusha's Contacts Search & Enrich.

Input:  sourced_contacts rows where batch_number = 2 AND (email IS NULL OR '')
        — expects 73 rows: 20 Clay + 53 LinkedIn/PB, all have linkedin_url.

Flow:
  1. Batch the missing-email contacts into groups of ≤100.
  2. POST /v3/contacts/search-and-enrich with each contact identified by
     linkedinUrl (fallback: firstName+lastName+companyDomain).
     reveal=["emails"] — we don't care about phones for gifting.
  3. Match responses back to our contacts (by linkedinUrl or the ordinal
     position depending on what Lusha returns).
  4. Update sourced_contacts.email for each hit; leave others alone.
  5. Write a delta CSV to data/batch2_lusha_email_delta.csv.

Docs: https://docs.lusha.com/apis/openapi/enrich/searchandenrichcontacts
Auth header: api_key: <LUSHA_API_KEY>
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

LUSHA_URL   = "https://api.lusha.com/v3/contacts/search-and-enrich"
API_KEY     = os.environ["LUSHA_API_KEY"]
BATCH_LIMIT = 100
OUT_CSV     = Path("data/batch2_lusha_email_delta.csv")


def _canonical_linkedin(li: str | None) -> str | None:
    """Lusha wants https://www.linkedin.com/in/<slug>. Our column stores
    the normalised form linkedin.com/in/<slug>. Reattach the scheme."""
    if not li:
        return None
    li = li.strip()
    if li.startswith("http"):
        return li
    if li.startswith("linkedin.com"):
        return "https://www." + li
    if li.startswith("www.linkedin.com"):
        return "https://" + li
    return li  # give it best-effort


def build_lookup_payload(contacts: list[dict]) -> list[dict]:
    """One dict per contact. Prefer linkedinUrl; fall back to name+domain.
    Lusha rejects unknown properties, so we match responses back by
    position (ordinal index) OR LinkedIn URL echoed in socialLinks."""
    payload = []
    for c in contacts:
        li = _canonical_linkedin(c.get("linkedin_url"))
        if li:
            payload.append({"linkedinUrl": li})
            continue
        payload.append({
            "firstName":     c.get("first_name") or "",
            "lastName":      c.get("last_name") or "",
            "companyDomain": c.get("domain") or "",
        })
    return payload


def call_lusha(contacts_payload: list[dict]) -> dict:
    resp = httpx.post(
        LUSHA_URL,
        headers={"api_key": API_KEY, "Content-Type": "application/json"},
        json={"contacts": contacts_payload, "reveal": ["emails"]},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()
    return resp.json()


def extract_email(result_row: dict) -> tuple[str | None, str | None]:
    """(email, confidence) or (None, None) if nothing usable."""
    emails = result_row.get("emails") or []
    if not emails:
        return None, None
    # Prefer work email, then highest confidence
    def rank(e):
        conf = (e.get("confidence") or "").upper()
        conf_rank = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(conf, 0)
        is_work = 1 if (e.get("type") == "work") else 0
        return (is_work, conf_rank)
    emails_sorted = sorted(emails, key=rank, reverse=True)
    best = emails_sorted[0]
    return best.get("email"), best.get("confidence")


def main() -> None:
    sb = get_supabase()
    rows = sb.table("sourced_contacts").select(
        "id,domain,company_name,first_name,last_name,linkedin_url,email,source"
    ).eq("batch_number", 2).or_("email.is.null,email.eq.").execute().data
    # supabase-py doesn't do IS NULL + OR cleanly; filter in Python for safety
    rows = [r for r in rows if not (r.get("email") or "").strip()]
    print(f"contacts missing email: {len(rows)}")

    findings: list[dict] = []
    updates_made = 0

    for i in range(0, len(rows), BATCH_LIMIT):
        chunk = rows[i:i + BATCH_LIMIT]
        payload = build_lookup_payload(chunk)
        print(f"\n▶ Lusha call {i//BATCH_LIMIT + 1}: {len(payload)} contacts")
        data = call_lusha(payload)
        billing = data.get("billing", {})
        print(f"  billing: charged={billing.get('creditsCharged')} returned={billing.get('resultsReturned')}")
        # First-batch debug: dump one successful and one errored result
        if i == 0:
            print(f"  response top-level keys: {list(data.keys())}")
            samples = data.get("contacts") or data.get("results") or []
            success = next((r for r in samples if "error" not in r), None)
            err     = next((r for r in samples if "error" in r), None)
            if success:
                print(f"  SUCCESS result keys: {list(success.keys())}")
                print(f"  SUCCESS payload: {json.dumps(success, indent=2)[:2000]}")
            if err:
                print(f"  ERROR sample: {json.dumps(err)}")
            # Show ALL results that have emails
            with_emails = [r for r in samples if r.get("emails")]
            print(f"  results with any emails: {len(with_emails)}")
            for r in with_emails[:5]:
                print(f"    → {r.get('fullName')} | linkedin={ (r.get('socialLinks') or {}).get('linkedin') } | emails={r.get('emails')}")

        # Match responses back by ORDINAL POSITION — Lusha returns results in
        # the exact order of the input `contacts` array, with error objects
        # inline for any that couldn't be found. We can't match by LinkedIn
        # URL because PB Sales Nav stores the obfuscated lead-ID form
        # (linkedin.com/in/ACwAAA...) while Lusha returns the clean vanity
        # URL (linkedin.com/in/louise-sweeney-42822b5b) — no overlap.
        results = data.get("results") or data.get("contacts") or []
        if len(results) != len(chunk):
            print(f"  ⚠️  response has {len(results)} rows, expected {len(chunk)} — "
                  f"ordinal matching may be off")

        for idx, c in enumerate(chunk):
            r = results[idx] if idx < len(results) else None
            email, conf = (None, None)
            if r and "error" not in r:
                email, conf = extract_email(r)
            findings.append({
                "contact_id":       c["id"],
                "first_name":       c["first_name"],
                "last_name":        c["last_name"],
                "company_name":     c["company_name"],
                "domain":           c["domain"],
                "source":           c["source"],
                "linkedin_url":     c["linkedin_url"],
                "email_found":      email or "",
                "confidence":       conf or "",
                "lusha_returned":   bool(r),
            })
            if email:
                sb.table("sourced_contacts").update({"email": email}).eq("id", c["id"]).execute()
                updates_made += 1

    # Write delta CSV
    OUT_CSV.parent.mkdir(exist_ok=True, parents=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()) if findings else [])
        w.writeheader()
        for row in findings:
            w.writerow(row)

    # Summary
    hits = sum(1 for f in findings if f["email_found"])
    print("\n" + "=" * 60)
    print(f"Total contacts checked:  {len(findings)}")
    print(f"Emails found + written:  {hits}  ({hits/len(findings)*100:.0f}%)")
    print(f"No email available:      {len(findings) - hits}")
    print(f"Delta CSV:               {OUT_CSV}")


if __name__ == "__main__":
    main()
