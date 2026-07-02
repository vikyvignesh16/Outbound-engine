"""Enrich physical-gifting office addresses for batch #2 contacts.

Hybrid per-contact approach:
  - For each contact, ask Claude Haiku 4.5 (with web_search) to find the
    SPECIFIC office where this person likely works.
  - Uses the contact's LinkedIn URL + city + company city as hints.
  - Falls back to primary HQ when the person's office can't be pinned down.

Deduplication:
  Multiple contacts at the same (domain, effective_city) get ONE Claude call
  and share the resulting address — cuts cost to ~90 calls for 225 contacts.

Output:
  scratchpad/batch2_gifting_addresses.csv — one row per contact with
  street/city/postcode/country + matched_to + confidence + Claude notes.
"""
import asyncio
import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values
os.environ.update({k: v for k, v in dotenv_values('.env').items() if v})

import anthropic
from db.client import get_supabase

MODEL          = "claude-haiku-4-5"
MAX_INFLIGHT   = 5
MAX_TOKENS     = 2000
MAX_WEB_SEARCH = 3

SCRATCH = Path("/private/tmp/claude-501/-Users-vigneshwar-kamaraj-Vignesh-Python-Brevo-ABM-V2/"
               "7c156464-5638-424c-8b98-4a1ebd4524b7/scratchpad")

SYSTEM_PROMPT = """You are enriching UK physical-gifting addresses. For each contact
I'll give you, use web_search to find the specific office this person commutes to.

Assumptions (do NOT deviate):
- The contact commutes to a physical office. Do NOT assume they work from home.
- Their LinkedIn location is the city they LIVE IN. Their office is usually the
  company office CLOSEST TO that city — within a reasonable UK commute radius
  (up to ~50 miles for London/SE, less for regional).

Rules:
- Use web_search — do NOT rely on memory alone.
- Enumerate the company's UK offices from their website / LinkedIn / Companies
  House if you're not sure. Companies with only ONE UK office → use that office
  regardless of the person's city (they commute in).
- Companies with 2+ UK offices → pick the office nearest the person's LinkedIn
  city. Hotel groups: pick the specific property the person likely works at
  (their job title + city usually narrows it down).
- For property-management groups (e.g. Bespoke Hotels manages 250+ hotels), the
  person may work at a specific managed property, not the group HQ. Search for
  their name + the group to see if they're publicly associated with a property.
- Return the final answer as a single JSON object with NO surrounding prose:
  {"street": "...", "city": "...", "region": "...", "postcode": "...",
   "country": "United Kingdom",
   "matched_to": "person_office|company_hq|city_unclear",
     - person_office: you picked a specific branch based on the person's city
     - company_hq:    company has only one office OR you couldn't narrow further
     - city_unclear:  no confident pick
   "confidence": "high|medium|low",
   "notes": "brief 1-line explanation of why this office"}
- If genuinely unfindable, return empty strings + confidence=low + notes.
"""


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _first_json_object(text: str) -> dict | None:
    """Extract the first {...} JSON object from Claude's response."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def lookup_one(client, key: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        user = (
            f"Company: {key['company_name']}\n"
            f"Domain: {key['domain']}\n"
            f"Contact LinkedIn city: {key['person_city'] or '(unknown)'}\n"
            f"Company LinkedIn city: {key['company_city'] or '(unknown)'}\n"
            f"Example contact: {key['sample_contact']} — {key['sample_title']}\n\n"
            f"Find the office address."
        )
        try:
            msg = await client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=[{"type": "web_search_20250305", "name": "web_search",
                        "max_uses": MAX_WEB_SEARCH}],
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            return {**key, "error": str(exc), "confidence": "low"}

        text = "\n".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        obj = _first_json_object(text)
        if not obj:
            return {**key, "error": "no_json", "raw_response": text[:400], "confidence": "low"}
        return {**key, **obj}


async def main() -> None:
    sb = get_supabase()
    contacts = sb.table("sourced_contacts").select(
        "id,domain,company_name,first_name,last_name,job_title,email,linkedin_url,raw,source"
    ).eq("batch_number", 2).execute().data
    print(f"loaded {len(contacts)} contacts from batch 2")

    # Build per-contact enrichment key with locations from raw jsonb
    for c in contacts:
        raw = c.get("raw") or {}
        c["person_city"]  = (raw.get("location") or "").strip()
        c["company_city"] = (raw.get("companyLocation") or "").strip()

    # Dedupe: group by (domain, person_city). Same city + same company = same office.
    groups: dict[tuple, list] = {}
    for c in contacts:
        k = (c["domain"], c["person_city"] or c["company_city"] or "")
        groups.setdefault(k, []).append(c)

    lookup_keys = []
    for (domain, city_hint), cs in groups.items():
        first = cs[0]
        lookup_keys.append({
            "domain":         domain,
            "company_name":   first["company_name"],
            "person_city":    first["person_city"],
            "company_city":   first["company_city"],
            "sample_contact": f"{first['first_name']} {first['last_name']}",
            "sample_title":   first["job_title"] or "",
            "_contacts":      cs,
        })
    print(f"deduped to {len(lookup_keys)} unique (domain × city) lookups")

    # Concurrently look up each
    client = _client()
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[lookup_one(client, k, sem) for k in lookup_keys])
    print(f"got {len(results)} responses back")

    # Build a map from (domain, city_hint) -> address dict
    addr_by_key: dict[tuple, dict] = {}
    for k, r in zip(lookup_keys, results):
        addr_by_key[(k["domain"], k["person_city"] or k["company_city"] or "")] = r

    # Write CSV: one row per contact
    SCRATCH.mkdir(parents=True, exist_ok=True)
    csv_path = SCRATCH / "batch2_gifting_addresses.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "company_name", "domain", "source",
            "first_name", "last_name", "job_title", "email", "linkedin_url",
            "person_linkedin_city",
            "office_street", "office_city", "office_region", "office_postcode",
            "office_country", "address_matched_to", "address_confidence", "address_notes",
        ])
        for c in contacts:
            key = (c["domain"], c["person_city"] or c["company_city"] or "")
            a = addr_by_key.get(key, {})
            w.writerow([
                c["company_name"], c["domain"], c["source"],
                c["first_name"], c["last_name"], c["job_title"] or "",
                c["email"] or "", c["linkedin_url"] or "",
                c["person_city"],
                a.get("street", ""), a.get("city", ""), a.get("region", ""),
                a.get("postcode", ""), a.get("country", ""),
                a.get("matched_to", ""), a.get("confidence", ""),
                a.get("notes", "") or a.get("error", ""),
            ])

    print(f"\n✅ wrote {len(contacts)} contact rows → {csv_path}")

    # Confidence summary
    from collections import Counter
    conf_counts = Counter(a.get("confidence") for a in addr_by_key.values())
    matched_counts = Counter(a.get("matched_to") for a in addr_by_key.values())
    print("\nConfidence breakdown (per unique lookup):")
    for c, n in conf_counts.most_common():
        print(f"  {c or '(none)':<10} {n}")
    print("\nMatched-to breakdown:")
    for m, n in matched_counts.most_common():
        print(f"  {m or '(none)':<20} {n}")


if __name__ == "__main__":
    asyncio.run(main())
