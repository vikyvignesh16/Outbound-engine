"""Enrich the Senior Marketing Connections CSV: LinkedIn location + email +
office address for physical gifting.

CSV in:  data/Senior Marketing Connections - Contacts by Title _ Marketing.csv
CSV out: data/senior_marketing_enriched.csv

One-shot enrichment on the user's personal LinkedIn network. No DB writes.
Contacts are UK + international (verified 2026-07-02 via 10-contact sample).

Flow:
  1. Read CSV, filter blank separator rows
  2. Claude Haiku + web_search → LinkedIn location (city + country). This is
     the authoritative location source — more reliable than Lusha for
     small/international companies. See probe results 2026-07-02: caught
     Adam Gardiner (London) + Sedki Alimam (Uppsala, Sweden) that Lusha missed.
  3. Lusha /v3/contacts/search-and-enrich → email
  4. Apollo /v1/people/bulk_match on residuals → email
  5. Claude Haiku + web_search → office address in the contact's ACTUAL country
     (UK contacts get UK offices, US contacts get US offices, etc.)
  6. Write final CSV

Reuses the same ordinal-position matching pattern as batch #2 gifting scripts.
See project memory: project-batch-2-gifting.
"""
import asyncio
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values
os.environ.update({k: v for k, v in dotenv_values('.env').items() if v})

import anthropic
import httpx

# ── Config ────────────────────────────────────────────────────────────────
CSV_IN  = Path("data/Senior Marketing Connections - Contacts by Title _ Marketing.csv")
CSV_OUT = Path("data/senior_marketing_enriched.csv")

LUSHA_URL      = "https://api.lusha.com/v3/contacts/search-and-enrich"
LUSHA_KEY      = os.environ["LUSHA_API_KEY"]
LUSHA_BATCH    = 100

APOLLO_URL     = "https://api.apollo.io/api/v1/people/bulk_match"
APOLLO_KEY     = os.environ["APOLLO_API_KEY"]
APOLLO_BATCH   = 10

MODEL          = "claude-haiku-4-5"
MAX_INFLIGHT   = 5
MAX_TOKENS     = 2000
MAX_WEB_SEARCH = 3

LOCATION_PROMPT = """You are looking up a contact's LinkedIn location. Use web_search
to find their LinkedIn profile snippet — the "Location" field is typically shown
in search results even without logging in.

Return a single JSON object with NO surrounding prose:
{"city": "...", "country": "...", "region": "...",
 "source": "linkedin|search_snippet|inferred",
 "confidence": "high|medium|low",
 "raw_location_text": "..."}

If you truly cannot find the location, return empty strings + confidence=low.
"""

ADDRESS_PROMPT = """You are enriching physical-gifting office addresses. For each
contact I'll give you, use web_search to find the office they commute to.

Assumptions (do NOT deviate):
- The contact's LinkedIn location is where they LIVE. Their office is usually
  the company office CLOSEST TO that city — within a reasonable commute.
- The contact commutes to a physical office. Do NOT assume they work from home.
- Ship to the office in the contact's ACTUAL country (as given by LinkedIn).
  UK contacts get UK offices. US contacts get US offices. Etc.
- Only if the company has no office in the contact's country, fall back to the
  primary HQ wherever it is.

Rules:
- Use web_search — do NOT rely on memory alone.
- Enumerate the company's offices in the contact's country. If only ONE office
  exists in-country, use it. If 2+, pick the one nearest the contact's city.
- Return the final answer as a single JSON object with NO surrounding prose:
  {"street": "...", "city": "...", "region": "...", "postcode": "...",
   "country": "...",
   "matched_to": "person_office|company_hq|country_hq_fallback|no_office_found",
     - person_office:       specific branch near the person's city
     - company_hq:          only one office in their country OR couldn't narrow
     - country_hq_fallback: no office in their country, shipped to global HQ
     - no_office_found:     no physical office you could verify
   "confidence": "high|medium|low",
   "notes": "brief 1-line explanation"}
- If genuinely unfindable, return empty strings + confidence=low + notes.
"""


# ── Helpers ───────────────────────────────────────────────────────────────
def _canonical_linkedin(url: str | None) -> str | None:
    """Normalise LinkedIn URL to https://www.linkedin.com/in/<slug> form."""
    if not url:
        return None
    u = url.strip()
    if not u:
        return None
    if u.startswith("http"):
        return u
    if u.startswith("linkedin.com"):
        return "https://www." + u
    if u.startswith("www.linkedin.com"):
        return "https://" + u
    return u


def read_contacts(csv_path: Path) -> list[dict]:
    """Read + filter the LinkedIn connections CSV."""
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        first = (r.get("First Name") or "").strip()
        last  = (r.get("Last Name")  or "").strip()
        url   = (r.get("URL")        or "").strip()
        if not url or not (first or last):
            continue  # blank separator rows
        out.append({
            "first_name":   first,
            "last_name":    last,
            "linkedin_url": url,
            "company":      (r.get("Company")  or "").strip(),
            "position":     (r.get("Position") or "").strip(),
            "connected_on": (r.get("Connected On") or "").strip(),
        })
    return out


# ── Lusha ─────────────────────────────────────────────────────────────────
def call_lusha(payload: list[dict]) -> dict:
    resp = httpx.post(
        LUSHA_URL,
        headers={"api_key": LUSHA_KEY, "Content-Type": "application/json"},
        json={"contacts": payload, "reveal": ["emails"]},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  Lusha {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()
    return resp.json()


def lusha_extract(row: dict) -> tuple[str | None, str | None, dict]:
    """Return (email, confidence, location_dict)."""
    if not row or "error" in row:
        return None, None, {}
    emails = row.get("emails") or []

    def rank(e):
        conf = (e.get("confidence") or "").upper()
        conf_rank = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(conf, 0)
        is_work = 1 if (e.get("type") == "work") else 0
        return (is_work, conf_rank)

    email, confidence = None, None
    if emails:
        best = sorted(emails, key=rank, reverse=True)[0]
        email = best.get("email")
        confidence = best.get("confidence")

    # Lusha returns location as top-level or nested — try a few keys
    loc = {
        "city":    row.get("location", {}).get("city") if isinstance(row.get("location"), dict) else row.get("city"),
        "country": row.get("location", {}).get("country") if isinstance(row.get("location"), dict) else row.get("country"),
    }
    return email, confidence, loc


def run_lusha(contacts: list[dict]) -> list[dict]:
    print(f"\n▶ Lusha pass: {len(contacts)} contacts")
    for i in range(0, len(contacts), LUSHA_BATCH):
        chunk = contacts[i:i + LUSHA_BATCH]
        payload = [{"linkedinUrl": _canonical_linkedin(c["linkedin_url"])} for c in chunk]
        try:
            data = call_lusha(payload)
        except httpx.HTTPStatusError:
            print("  Lusha call failed, skipping chunk")
            continue
        billing = data.get("billing", {}) or {}
        print(f"  batch {i//LUSHA_BATCH + 1}: charged={billing.get('creditsCharged')} "
              f"returned={billing.get('resultsReturned')}")
        results = data.get("results") or data.get("contacts") or []
        if len(results) != len(chunk):
            print(f"  ⚠️  {len(results)} results vs {len(chunk)} inputs — ordinal may drift")
        for idx, c in enumerate(chunk):
            r = results[idx] if idx < len(results) else None
            email, conf, loc = lusha_extract(r)
            c["email"]          = email
            c["email_source"]   = "lusha" if email else None
            c["email_confidence"] = conf
            c["contact_city"]    = loc.get("city")
            c["contact_country"] = loc.get("country")
        time.sleep(0.3)
    hits = sum(1 for c in contacts if c.get("email"))
    print(f"  Lusha filled: {hits}/{len(contacts)} ({hits/len(contacts)*100:.0f}%)")
    return contacts


# ── Apollo ────────────────────────────────────────────────────────────────
def call_apollo(details: list[dict]) -> dict:
    resp = httpx.post(
        APOLLO_URL,
        headers={"Content-Type": "application/json", "Cache-Control": "no-cache",
                 "accept": "application/json", "X-Api-Key": APOLLO_KEY},
        json={"details": details, "reveal_personal_emails": True},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  Apollo {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()
    return resp.json()


def apollo_extract(match: dict | None) -> tuple[str | None, str | None, dict]:
    """Return (email, status, location_dict)."""
    if not match:
        return None, None, {}
    email = (match.get("email") or "").strip()
    status = match.get("email_status") or ""
    if not email:
        personals = match.get("personal_emails") or []
        if personals and personals[0]:
            email = personals[0].strip()
            status = status or "personal"
    loc = {"city": match.get("city"), "country": match.get("country")}
    return (email or None), status, loc


def run_apollo(contacts: list[dict]) -> list[dict]:
    residual = [c for c in contacts if not c.get("email")]
    print(f"\n▶ Apollo pass on residual: {len(residual)} contacts")
    for i in range(0, len(residual), APOLLO_BATCH):
        chunk = residual[i:i + APOLLO_BATCH]
        details = [{"linkedin_url": _canonical_linkedin(c["linkedin_url"])} for c in chunk]
        try:
            data = call_apollo(details)
        except httpx.HTTPStatusError:
            print("  Apollo call failed, skipping chunk")
            continue
        matches = data.get("matches") or []
        for idx, c in enumerate(chunk):
            m = matches[idx] if idx < len(matches) else None
            email, status, loc = apollo_extract(m)
            if email:
                c["email"]          = email
                c["email_source"]   = "apollo"
                c["email_confidence"] = status
            # Even if no email, take Apollo's location if Lusha didn't have it
            if not c.get("contact_city") and loc.get("city"):
                c["contact_city"] = loc["city"]
            if not c.get("contact_country") and loc.get("country"):
                c["contact_country"] = loc["country"]
        time.sleep(0.3)
    hits = sum(1 for c in residual if c.get("email"))
    print(f"  Apollo filled: {hits}/{len(residual)}")
    return contacts


# ── Claude enrichment (shared helpers) ────────────────────────────────────
def _first_json(text: str) -> dict | None:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def _claude_web_search(client, system: str, user: str) -> dict:
    try:
        msg = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=[{"type": "web_search_20250305", "name": "web_search",
                    "max_uses": MAX_WEB_SEARCH}],
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:
        return {"error": str(exc), "confidence": "low"}
    text = "\n".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    obj = _first_json(text)
    if not obj:
        return {"error": "no_json", "raw": text[:300], "confidence": "low"}
    return obj


# ── Step: LinkedIn location lookup ────────────────────────────────────────
async def lookup_linkedin_location(client, c: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        user = (
            f"Name: {c['first_name']} {c['last_name']}\n"
            f"Company: {c['company']}\n"
            f"LinkedIn URL: {c['linkedin_url']}\n"
            f"Position: {c['position']}\n\n"
            f"Find the LinkedIn 'Location' field for this person."
        )
        return await _claude_web_search(client, LOCATION_PROMPT, user)


async def run_linkedin_locations(contacts: list[dict]) -> list[dict]:
    print(f"\n▶ LinkedIn location lookup: {len(contacts)} contacts (Claude Haiku + web_search)")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[lookup_linkedin_location(client, c, sem) for c in contacts])
    for c, r in zip(contacts, results):
        c["linkedin_city"]        = r.get("city", "") or ""
        c["linkedin_country"]     = r.get("country", "") or ""
        c["linkedin_region"]      = r.get("region", "") or ""
        c["location_source"]      = r.get("source", "")
        c["location_confidence"]  = r.get("confidence", "")
        c["location_raw"]         = r.get("raw_location_text") or r.get("error") or ""
    hits = sum(1 for c in contacts if c.get("linkedin_city") or c.get("linkedin_country"))
    print(f"  location filled: {hits}/{len(contacts)}")
    from collections import Counter
    countries = Counter(c["linkedin_country"] for c in contacts if c.get("linkedin_country"))
    print(f"  country distribution: {dict(countries.most_common(10))}")
    return contacts


# ── Step: office address (uses LinkedIn location from step above) ─────────
async def lookup_address(client, c: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        user = (
            f"Company: {c['company']}\n"
            f"Contact LinkedIn URL: {c['linkedin_url']}\n"
            f"Contact LinkedIn city:    {c.get('linkedin_city') or '(unknown)'}\n"
            f"Contact LinkedIn country: {c.get('linkedin_country') or '(unknown)'}\n"
            f"Contact position: {c['position']}\n\n"
            f"Find the office address in the contact's country."
        )
        return await _claude_web_search(client, ADDRESS_PROMPT, user)


async def run_addresses(contacts: list[dict]) -> list[dict]:
    print(f"\n▶ Office address lookup: {len(contacts)} contacts (Claude Haiku + web_search)")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[lookup_address(client, c, sem) for c in contacts])
    for c, r in zip(contacts, results):
        c["office_street"]   = r.get("street", "")
        c["office_city"]     = r.get("city", "")
        c["office_region"]   = r.get("region", "")
        c["office_postcode"] = r.get("postcode", "")
        c["office_country"]  = r.get("country", "")
        c["address_matched_to"] = r.get("matched_to", "")
        c["address_confidence"] = r.get("confidence", "")
        c["address_notes"]      = r.get("notes") or r.get("error") or ""
    return contacts


# ── Main ──────────────────────────────────────────────────────────────────
def write_csv(contacts: list[dict]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "first_name", "last_name", "company", "position", "linkedin_url",
        "email", "email_source", "email_confidence",
        "linkedin_city", "linkedin_region", "linkedin_country",
        "location_source", "location_confidence", "location_raw",
        "office_street", "office_city", "office_region", "office_postcode",
        "office_country", "address_matched_to", "address_confidence", "address_notes",
        "connected_on",
    ]
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for c in contacts:
            w.writerow(c)
    print(f"\n✅ Wrote {len(contacts)} rows → {CSV_OUT}")


async def main() -> None:
    contacts = read_contacts(CSV_IN)
    print(f"Loaded {len(contacts)} contacts (after filtering blank rows)")

    # Step 1: LinkedIn location (authoritative) — must precede address step
    await run_linkedin_locations(contacts)
    # Step 2 + 3: emails
    run_lusha(contacts)
    run_apollo(contacts)
    # Step 4: office address using LinkedIn location
    await run_addresses(contacts)

    write_csv(contacts)

    from collections import Counter
    email_by_source = Counter(c.get("email_source") for c in contacts if c.get("email"))
    addr_conf       = Counter(c.get("address_confidence") for c in contacts)
    addr_matched    = Counter(c.get("address_matched_to") for c in contacts)
    country_dist    = Counter(c.get("linkedin_country") for c in contacts if c.get("linkedin_country"))
    total_email     = sum(1 for c in contacts if c.get("email"))
    total_location  = sum(1 for c in contacts if c.get("linkedin_country"))

    print("\n" + "=" * 60)
    print(f"Location:  {total_location}/{len(contacts)} contacts got a LinkedIn location")
    print(f"  country distribution: {dict(country_dist.most_common(10))}")
    print(f"Email:     {total_email}/{len(contacts)} = {total_email/len(contacts)*100:.0f}%")
    print(f"  by source: {dict(email_by_source)}")
    print(f"Address confidence: {dict(addr_conf)}")
    print(f"Address matched_to: {dict(addr_matched)}")


if __name__ == "__main__":
    asyncio.run(main())
