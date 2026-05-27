import asyncio
import json
import logging
import os

import httpx
from fastapi import APIRouter

from db.client import get_supabase, fetch_all

logger = logging.getLogger(__name__)
router = APIRouter()

TECHNOGRAPHIC_BASE_URL = "http://t8kcgcskw0g0oco0g0ckwsgo.77.42.64.109.sslip.io"
BREVO_CRM_BASE_URL = "https://api.brevo.com/v3"

# (keywords, score) — checked in order; first match wins per ESP entry
COMPETITOR_ESP_SCORES: list[tuple[set[str], int]] = [
    ({"mailchimp", "mandrill", "activecampaign", "constant contact",
      "omnisend", "mailerlite", "getresponse", "campaign monitor"}, 100),
    ({"sendgrid", "mailgun", "postmark", "sparkpost", "amazon ses"}, 75),
    ({"barracuda", "unknown"}, 50),
    ({"hubspot", "braze", "segment", "mparticle", "klaviyo"}, 25),
    ({"salesforce", "marketo", "adobe", "microsoft dynamics"}, 0),
]
_DEFAULT_ESP_SCORE = 50


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _score_one_esp(name: str) -> int:
    lowered = name.lower()
    for keywords, score in COMPETITOR_ESP_SCORES:
        if any(k in lowered for k in keywords):
            return score
    return _DEFAULT_ESP_SCORE


def compute_esp_score(esp_list: list[dict]) -> int:
    """Returns highest competitor score across all detected ESPs. 0 if none."""
    if not esp_list:
        return 0
    return max(_score_one_esp(e.get("name", "")) for e in esp_list)


def get_primary_esp(esp_list: list[dict]) -> str | None:
    """Returns the name of the ESP with the highest competitor score."""
    if not esp_list:
        return None
    return max(esp_list, key=lambda e: _score_one_esp(e.get("name", ""))).get("name")


# ── Brevo CRM API call ────────────────────────────────────────────────────────

async def get_brevo_company(domain: str, client: httpx.AsyncClient) -> dict | None:
    """
    Calls Brevo CRM API to find a company by domain.
    Returns a normalised dict with all four CRM fields, or None if not found.
    Retries on 429 and 500 with exponential backoff.
    """
    url = f"{BREVO_CRM_BASE_URL}/companies"
    headers = {"api-key": os.environ["BREVO_CRM_API_KEY"]}
    params = {"filters": json.dumps({"attributes.domain": domain})}

    for attempt, wait in enumerate([0, 1, 2, 4]):
        if wait:
            await asyncio.sleep(wait)
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=15.0)
            if resp.status_code in (429, 500) and attempt < 3:
                logger.warning("brevo_crm: %d for %s, retrying (attempt %d)", resp.status_code, domain, attempt + 1)
                continue
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                return None
            item = items[0]
            attrs = item.get("attributes", {})
            return {
                "brevo_company_id": item.get("id"),
                "open_deals":       attrs.get("ent_nb_open_deals"),
                "deal_lost_date":   attrs.get("ent_last_lost_deal_date"),
                "planhat_id":       attrs.get("ent_planhat_id") or None,
            }
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (429, 500) and attempt < 3:
                continue
            raise
    raise RuntimeError(f"brevo_crm: all retries exhausted for {domain}")


# ── Step 2: CRM check ─────────────────────────────────────────────────────────

async def run_crm_check() -> dict:
    """
    Reads all rows from sourced_tam_v2, calls Brevo CRM API once per domain,
    and writes all four CRM fields back (brevo_company_id, open_deals,
    deal_lost_date, planhat_id). Domains not found in CRM get null for all four.
    """
    sb = get_supabase()
    rows = fetch_all("sourced_tam_v2", "domain, market")

    if not rows:
        logger.info("crm_check: no rows to process")
        return {"status": "ok", "processed": 0}

    logger.info("crm_check: processing %d domains", len(rows))
    semaphore = asyncio.Semaphore(25)

    async def fetch_one(row: dict) -> None:
        domain = row["domain"]
        async with semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    crm = await get_brevo_company(domain, client)
                update_payload = crm if crm else {
                    "brevo_company_id": None,
                    "open_deals":       None,
                    "deal_lost_date":   None,
                    "planhat_id":       None,
                }
                sb.table("sourced_tam_v2").update(update_payload).eq("domain", domain).eq("market", row["market"]).execute()
            except Exception as exc:
                logger.error("crm_check: failed for %s: %s", domain, exc)

    await asyncio.gather(*[fetch_one(r) for r in rows])
    logger.info("crm_check: wrote crm fields for %d domains", len(rows))
    return {"status": "ok", "processed": len(rows)}


# ── Step 3: Qualification rules ───────────────────────────────────────────────

def apply_rules(row: dict) -> tuple[bool, str | None]:
    """
    Pure function. Returns (qualifies, disqualification_reason).

    Rules (evaluated in order):
    1. No brevo_company_id → new prospect → qualifies
    2. Has brevo_company_id + planhat_id → existing customer → disqualify
    3. Has brevo_company_id + open_deals > 0 + no deal_lost_date → active deal → disqualify
    4. Everything else → qualifies (former prospect or lost deal)
    """
    brevo_id = row.get("brevo_company_id")
    planhat_id = row.get("planhat_id")
    open_deals = row.get("open_deals") or 0
    deal_lost_date = row.get("deal_lost_date")

    if not brevo_id:
        return True, None

    if planhat_id:
        return False, "existing_customer"

    if open_deals > 0 and not deal_lost_date:
        return False, "open_deal_exists"

    return True, None


async def run_qualification_rules() -> dict:
    """
    Reads all rows from sourced_tam_v2, applies qualification rules,
    and upserts qualifying rows into qualified_tam_v2.
    """
    sb = get_supabase()
    rows = fetch_all(
        "sourced_tam_v2",
        "id, domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date",
    )

    qualified_rows = []
    disqualified = 0

    for row in rows:
        qualifies, _ = apply_rules(row)
        if qualifies:
            qualified_rows.append({
                "sourced_tam_id":    row["id"],
                "domain":            row["domain"],
                "market":            row["market"],
                "company_name":      row.get("company_name"),
                "company_type":      row.get("company_type"),
                "employee_range":    row.get("employee_range"),
                "location":          row.get("location"),
                "country":           row.get("country"),
                "linkedin_url":      row.get("linkedin_url"),
                "vertical":          row.get("vertical"),
                "brevo_company_id":  row.get("brevo_company_id"),
                "planhat_id":        row.get("planhat_id"),
                "open_deals":        row.get("open_deals"),
                "deal_lost_date":    row.get("deal_lost_date"),
            })
        else:
            disqualified += 1

    # keep only the highest sourced_tam_id row per (domain, market)
    best: dict[tuple, dict] = {}
    for r in qualified_rows:
        key = (r["domain"], r["market"])
        if key not in best or r["sourced_tam_id"] > best[key]["sourced_tam_id"]:
            best[key] = r
    deduped = list(best.values())

    if deduped:
        for i in range(0, len(deduped), 100):
            chunk = deduped[i : i + 100]
            sb.table("qualified_tam_v2").upsert(chunk, on_conflict="domain,market").execute()

    logger.info("qualification_rules: qualified=%d deduped=%d disqualified=%d", len(qualified_rows), len(deduped), disqualified)
    return {"status": "ok", "qualified": len(deduped), "disqualified": disqualified}


# ── Technographic API call ────────────────────────────────────────────────────

async def get_techstack(domain: str, client: httpx.AsyncClient) -> dict:
    """Calls the Technographic API with exponential backoff on 500 errors."""
    url = f"{TECHNOGRAPHIC_BASE_URL}/api/techstack"
    headers = {"X-API-Key": os.environ["TECHNOGRAPHIC_API_KEY"]}
    params = {"domain": domain, "mode": "smart"}

    for attempt, wait in enumerate([0, 1, 2, 4]):
        if wait:
            await asyncio.sleep(wait)
        try:
            resp = await client.get(url, headers=headers, params=params, timeout=30.0)
            if resp.status_code == 500 and attempt < 3:
                logger.warning("techstack: 500 for %s, retrying (attempt %d)", domain, attempt + 1)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 500 and attempt < 3:
                continue
            raise
    raise RuntimeError(f"techstack: all retries exhausted for {domain}")


# ── Step 4: Technographic enrichment ─────────────────────────────────────────

async def run_technographic() -> dict:
    """
    Reads qualified_tam_v2 rows with no esp_score yet,
    calls Technographic API per domain, and writes esp_detected + esp_score back.
    """
    sb = get_supabase()
    rows = fetch_all("qualified_tam_v2", "domain, market", [("is_", "esp_score", "null")])

    if not rows:
        logger.info("technographic: no rows to process")
        return {"status": "ok", "processed": 0}

    logger.info("technographic: processing %d domains", len(rows))
    semaphore = asyncio.Semaphore(25)

    async def fetch_one(row: dict) -> dict | None:
        domain = row["domain"]
        async with semaphore:
            try:
                async with httpx.AsyncClient() as client:
                    data = await get_techstack(domain, client)
                esp_list = data.get("esp", [])
                return {
                    "domain":       domain,
                    "market":       row["market"],
                    "esp_detected": get_primary_esp(esp_list),
                    "esp_score":    compute_esp_score(esp_list),
                }
            except Exception as exc:
                logger.error("techstack: failed for %s: %s", domain, exc)
                return None

    results = await asyncio.gather(*[fetch_one(r) for r in rows])
    enriched = [r for r in results if r is not None]

    for result in enriched:
        sb.table("qualified_tam_v2").update({
            "esp_detected": result["esp_detected"],
            "esp_score":    result["esp_score"],
        }).eq("domain", result["domain"]).eq("market", result["market"]).execute()

    logger.info("technographic: wrote %d results", len(enriched))
    return {"status": "ok", "processed": len(enriched)}


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/pipelines/qualify")
async def run_qualification():
    """Runs Steps 2-4: CRM check → qualification rules → technographic enrichment."""
    crm = await run_crm_check()
    rules = await run_qualification_rules()
    tech = await run_technographic()
    return {"crm": crm, "rules": rules, "technographic": tech}
