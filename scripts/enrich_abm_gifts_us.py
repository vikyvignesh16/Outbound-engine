"""Enrich the US ABM Gifts list: source missing contacts + emails + office addresses.

CSV in:  data/ABMGifts_Q1_Q2_Field_open_deals - Sheet2.csv
CSV out: data/abm_gifts_us_enriched.csv

42 rows total: 20 already have a real contact, 22 need contact sourcing.
The source CSV has a column-drift bug on rows 22-36 (Deal Name column drifted
down one row) — this script corrects it via a hand-verified COMPANY_DOMAIN map.

Flow:
  1. Read CSV, split into have-contact vs need-sourcing
  2. For need-sourcing: Claude Haiku + web_search finds a current marketing /
     CRM / ecommerce / retention decision-maker (Director / VP / C-suite).
     Priority list: CMO → VP Marketing → Director → Head of → Founder/CEO.
  3. Claude Haiku + web_search → LinkedIn city + country (authoritative
     location — same approach as scripts/enrich_senior_marketing_connections.py).
  4. Lusha /v3/contacts/search-and-enrich → email.
  5. Apollo /v1/people/bulk_match on residuals → email.
  6. Claude Haiku + web_search → office address in contact's country
     (US contacts get US offices).
  7. Write final CSV.

Reuses the same helpers + ordinal-position matching from the batch #2 and
senior-marketing scripts.
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
CSV_IN  = Path("data/ABMGifts_Q1_Q2_Field_open_deals - Sheet2.csv")
CSV_OUT = Path("data/abm_gifts_us_enriched.csv")

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


# Column-drift correction for source CSV rows 22-36 (Deal Name drifted).
# The Company column IS the correct account name; we hand-map the domain here.
COMPANY_DOMAIN_OVERRIDE = {
    "NRF":                              "nrf.com",
    "Highlights For Children":          "highlights.com",
    "Love Me Gluten Free":              "lovemeglutenfree.com",
    "History By Mail":                  "historybymail.com",
    "Good Ranchers":                    "goodranchers.com",
    "Good Protein":                     "goodprotein.com",
    "Ultra Pouches":                    "ultrapouches.com",
    "Ka'Chava":                         "kachava.com",
    "Transparent Labs":                 "transparentlabs.com",
    "Lifeaid Beverage Co. / Fitaid":    "lifeaidbeverage.com",
    "AARP":                             "aarp.com",
    "Suvie":                            "suvie.com",
    "Luma Nutrition":                   "lumanutrition.com",
    "Butcherbox":                       "butcherbox.com",
    "Ugly Sleep Club":                  "uglysleepclub.com",
    "Premier Pet Supply":               "premierpetsupply.com",
    "MasterClass":                      "masterclass.com",
}


# ── Prompts ───────────────────────────────────────────────────────────────
SOURCE_CONTACT_PROMPT = """You are sourcing a decision-maker contact at a US company
for a Brevo (email marketing / CRM platform) outbound conversation. Use web_search
to find the best-fit person currently at the target company.

Priority (in order):
  1. CMO / Chief Marketing Officer
  2. VP Marketing / VP Growth / VP Digital / VP CRM
  3. Director of Marketing / CRM / Retention / Ecommerce / Digital / Growth
  4. Head of Marketing / Growth / CRM / Ecommerce
  5. Founder / CEO (only for very small companies where the above roles don't exist)

Return a single JSON object with NO surrounding prose:
{"first_name": "...", "last_name": "...", "title": "...",
 "linkedin_url": "https://www.linkedin.com/in/...",
 "confidence": "high|medium|low",
 "reason": "why this person is the best fit + source URL"}

If no confident match, return empty strings + confidence=low + reason.
"""

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
  US contacts get US offices. UK contacts get UK offices. Etc.
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
   "confidence": "high|medium|low",
   "notes": "brief 1-line explanation"}
- If genuinely unfindable, return empty strings + confidence=low + notes.
"""


# ── Helpers ───────────────────────────────────────────────────────────────
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


def _canonical_linkedin(url: str | None) -> str | None:
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


async def _claude_web_search(client, system: str, user: str) -> dict:
    try:
        msg = await client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=system,
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


# ── Step 1: read + split ──────────────────────────────────────────────────
def read_contacts(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    contacts = []
    for r in rows:
        company = (r.get("Company") or "").strip()
        if not company:
            continue

        # Resolve domain: override map wins, else use Deal Name column
        domain = COMPANY_DOMAIN_OVERRIDE.get(company) or (r.get("Deal Name") or "").strip() or None

        email = (r.get("Contact Email") or "").strip()
        has_real_contact = (
            email and "@" in email and email != "—" and not email.startswith("hold@")
        )

        contacts.append({
            "company":         company,
            "domain":          domain,
            "deal_stage":      (r.get("Deal Stage")  or "").strip(),
            "deal_owner":      (r.get("Deal Owner")  or "").strip(),
            "first_name":      (r.get("Contact First Name") or "").strip().replace("—", ""),
            "last_name":       (r.get("Contact Last Name")  or "").strip().replace("—", ""),
            "title":           (r.get("Contact Job Title") or "").strip().replace("—", ""),
            "email":           email if has_real_contact else "",
            "email_source":    "sheet" if has_real_contact else "",
            "linkedin_url":    "",
            "needs_sourcing":  not has_real_contact,
        })
    return contacts


# ── Step 2: source missing contacts (Claude + web_search) ─────────────────
async def source_one(client, c: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        user = (f"Company: {c['company']}\nDomain: {c['domain']}\n\n"
                f"Find the best marketing/CRM decision maker currently at this company.")
        return await _claude_web_search(client, SOURCE_CONTACT_PROMPT, user)


async def run_source_contacts(contacts: list[dict]) -> None:
    need = [c for c in contacts if c["needs_sourcing"]]
    print(f"\n▶ Sourcing contacts for {len(need)} companies (Claude Haiku + web_search)")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[source_one(client, c, sem) for c in need])
    for c, r in zip(need, results):
        c["first_name"]    = (r.get("first_name") or "").strip()
        c["last_name"]     = (r.get("last_name")  or "").strip()
        c["title"]         = (r.get("title")      or "").strip()
        c["linkedin_url"]  = _canonical_linkedin(r.get("linkedin_url")) or ""
        c["source_confidence"] = r.get("confidence", "")
        c["source_reason"]     = r.get("reason") or r.get("error") or ""
    hits = sum(1 for c in need if c.get("linkedin_url"))
    print(f"  sourced: {hits}/{len(need)}")


# ── Step 3: LinkedIn location ─────────────────────────────────────────────
async def loc_one(client, c: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        if not c.get("linkedin_url"):
            return {"confidence": "low", "error": "no_linkedin_url"}
        user = (f"Name: {c['first_name']} {c['last_name']}\n"
                f"Company: {c['company']}\n"
                f"LinkedIn URL: {c['linkedin_url']}\n"
                f"Position: {c['title']}\n\n"
                f"Find the LinkedIn 'Location' field for this person.")
        return await _claude_web_search(client, LOCATION_PROMPT, user)


async def run_linkedin_locations(contacts: list[dict]) -> None:
    print(f"\n▶ LinkedIn location lookup: {len(contacts)} contacts")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[loc_one(client, c, sem) for c in contacts])
    for c, r in zip(contacts, results):
        c["linkedin_city"]       = r.get("city", "") or ""
        c["linkedin_country"]    = r.get("country", "") or ""
        c["linkedin_region"]     = r.get("region", "") or ""
        c["location_confidence"] = r.get("confidence", "")
        c["location_raw"]        = r.get("raw_location_text") or r.get("error") or ""
    hits = sum(1 for c in contacts if c.get("linkedin_country"))
    print(f"  location filled: {hits}/{len(contacts)}")


# ── Step 4: Lusha email ───────────────────────────────────────────────────
def call_lusha(payload: list[dict]) -> dict:
    resp = httpx.post(
        LUSHA_URL,
        headers={"api_key": LUSHA_KEY, "Content-Type": "application/json"},
        json={"contacts": payload, "reveal": ["emails"]},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  Lusha {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()


def lusha_extract(row: dict) -> tuple[str | None, str | None]:
    if not row or "error" in row:
        return None, None
    emails = row.get("emails") or []
    if not emails:
        return None, None

    def rank(e):
        conf = (e.get("confidence") or "").upper()
        conf_rank = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(conf, 0)
        is_work = 1 if (e.get("type") == "work") else 0
        return (is_work, conf_rank)

    best = sorted(emails, key=rank, reverse=True)[0]
    return best.get("email"), best.get("confidence")


def run_lusha(contacts: list[dict]) -> None:
    # Only enrich contacts we don't already have an email for
    todo = [c for c in contacts if not c.get("email") and c.get("linkedin_url")]
    print(f"\n▶ Lusha pass on {len(todo)} contacts (skipping the 20 with sheet emails)")
    for i in range(0, len(todo), LUSHA_BATCH):
        chunk = todo[i:i + LUSHA_BATCH]
        payload = [{"linkedinUrl": _canonical_linkedin(c["linkedin_url"])} for c in chunk]
        try:
            data = call_lusha(payload)
        except httpx.HTTPStatusError:
            continue
        results = data.get("results") or data.get("contacts") or []
        for idx, c in enumerate(chunk):
            r = results[idx] if idx < len(results) else None
            email, conf = lusha_extract(r)
            if email:
                c["email"]          = email
                c["email_source"]   = "lusha"
                c["email_confidence"] = conf
        time.sleep(0.3)
    hits = sum(1 for c in todo if c.get("email"))
    print(f"  Lusha filled: {hits}/{len(todo)}")


# ── Step 5: Apollo email (residual) ───────────────────────────────────────
def call_apollo(details: list[dict]) -> dict:
    resp = httpx.post(
        APOLLO_URL,
        headers={"Content-Type":"application/json","Cache-Control":"no-cache",
                 "X-Api-Key":APOLLO_KEY,"accept":"application/json"},
        json={"details": details, "reveal_personal_emails": True},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ⚠️  Apollo {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()


def apollo_extract(m: dict | None) -> tuple[str | None, str | None]:
    if not m:
        return None, None
    email = (m.get("email") or "").strip()
    status = m.get("email_status") or ""
    if not email:
        p = m.get("personal_emails") or []
        if p and p[0]:
            email = p[0].strip()
            status = status or "personal"
    return (email or None), status


def run_apollo(contacts: list[dict]) -> None:
    todo = [c for c in contacts if not c.get("email") and c.get("linkedin_url")]
    print(f"\n▶ Apollo pass on {len(todo)} residual contacts")
    for i in range(0, len(todo), APOLLO_BATCH):
        chunk = todo[i:i + APOLLO_BATCH]
        details = [{"linkedin_url": _canonical_linkedin(c["linkedin_url"])} for c in chunk]
        try:
            data = call_apollo(details)
        except httpx.HTTPStatusError:
            continue
        matches = data.get("matches") or []
        for idx, c in enumerate(chunk):
            m = matches[idx] if idx < len(matches) else None
            email, status = apollo_extract(m)
            if email:
                c["email"]          = email
                c["email_source"]   = "apollo"
                c["email_confidence"] = status
        time.sleep(0.3)
    hits = sum(1 for c in todo if c.get("email"))
    print(f"  Apollo filled: {hits}/{len(todo)}")


# ── Step 6: office address ────────────────────────────────────────────────
async def addr_one(client, c: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        user = (f"Company: {c['company']} ({c.get('domain') or 'no domain'})\n"
                f"Contact: {c['first_name']} {c['last_name']} — {c.get('title','')}\n"
                f"Contact LinkedIn URL: {c.get('linkedin_url') or '(none)'}\n"
                f"Contact LinkedIn city:    {c.get('linkedin_city')    or '(unknown)'}\n"
                f"Contact LinkedIn country: {c.get('linkedin_country') or '(unknown)'}\n\n"
                f"Find the office address in the contact's country.")
        return await _claude_web_search(client, ADDRESS_PROMPT, user)


async def run_addresses(contacts: list[dict]) -> None:
    print(f"\n▶ Office address lookup: {len(contacts)} contacts")
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(MAX_INFLIGHT)
    results = await asyncio.gather(*[addr_one(client, c, sem) for c in contacts])
    for c, r in zip(contacts, results):
        c["office_street"]      = r.get("street", "")
        c["office_city"]        = r.get("city", "")
        c["office_region"]      = r.get("region", "")
        c["office_postcode"]    = r.get("postcode", "")
        c["office_country"]     = r.get("country", "")
        c["address_matched_to"] = r.get("matched_to", "")
        c["address_confidence"] = r.get("confidence", "")
        c["address_notes"]      = r.get("notes") or r.get("error") or ""


# ── Main ──────────────────────────────────────────────────────────────────
def write_csv(contacts: list[dict]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "company", "domain", "deal_stage", "deal_owner",
        "first_name", "last_name", "title", "linkedin_url",
        "email", "email_source", "email_confidence",
        "linkedin_city", "linkedin_region", "linkedin_country",
        "location_confidence", "location_raw",
        "source_confidence", "source_reason",
        "office_street", "office_city", "office_region", "office_postcode",
        "office_country", "address_matched_to", "address_confidence", "address_notes",
    ]
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for c in contacts:
            w.writerow(c)
    print(f"\n✅ Wrote {len(contacts)} rows → {CSV_OUT}")


async def main() -> None:
    contacts = read_contacts(CSV_IN)
    already = sum(1 for c in contacts if not c["needs_sourcing"])
    need    = sum(1 for c in contacts if c["needs_sourcing"])
    print(f"Loaded {len(contacts)} rows: {already} with existing contact, {need} need sourcing")

    await run_source_contacts(contacts)
    await run_linkedin_locations(contacts)
    run_lusha(contacts)
    run_apollo(contacts)
    await run_addresses(contacts)
    write_csv(contacts)

    from collections import Counter
    total_email    = sum(1 for c in contacts if c.get("email"))
    email_by_src   = Counter(c.get("email_source") for c in contacts if c.get("email"))
    country_dist   = Counter(c.get("linkedin_country") for c in contacts if c.get("linkedin_country"))
    addr_conf      = Counter(c.get("address_confidence") for c in contacts)
    addr_matched   = Counter(c.get("address_matched_to") for c in contacts)
    print("\n" + "=" * 60)
    print(f"Sourced contact LinkedIn URLs: {sum(1 for c in contacts if c.get('linkedin_url'))}/{len(contacts)}")
    print(f"Email:     {total_email}/{len(contacts)} = {total_email/len(contacts)*100:.0f}%")
    print(f"  by source: {dict(email_by_src)}")
    print(f"Country distribution: {dict(country_dist.most_common(10))}")
    print(f"Address confidence: {dict(addr_conf)}")
    print(f"Address matched_to: {dict(addr_matched)}")


if __name__ == "__main__":
    asyncio.run(main())
