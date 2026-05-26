import asyncio
import logging
import os

import httpx
from fastapi import APIRouter

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

TECHNOGRAPHIC_BASE_URL = "http://t8kcgcskw0g0oco0g0ckwsgo.77.42.64.109.sslip.io"

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


# ── Batch enrichment ──────────────────────────────────────────────────────────

async def enrich_batch(
    rows: list[dict],
    concurrency: int = 5,
) -> list[dict]:
    """
    Calls the Technographic API for each row concurrently (max `concurrency`).
    Returns list of dicts with domain, market, esp_detected, esp_score.
    Failed domains are logged and skipped (pipeline error pattern from SKILL.md §9).
    """
    semaphore = asyncio.Semaphore(concurrency)

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
    return [r for r in results if r is not None]


# ── Step 2 pipeline ───────────────────────────────────────────────────────────

async def run_step2() -> dict:
    """
    Reads all unqualified rows from sourced_tam_v2 (esp_score IS NULL),
    calls the Technographic API, and writes esp_detected + esp_score back.
    """
    sb = get_supabase()

    rows = (
        sb.table("sourced_tam_v2")
        .select("domain, market")
        .is_("esp_score", "null")
        .execute()
        .data
    )

    if not rows:
        logger.info("qualification step2: no unqualified rows found")
        return {"status": "ok", "processed": 0}

    logger.info("qualification step2: processing %d domains", len(rows))
    enriched = await enrich_batch(rows)

    for result in enriched:
        sb.table("sourced_tam_v2").update({
            "esp_detected": result["esp_detected"],
            "esp_score":    result["esp_score"],
        }).eq("domain", result["domain"]).eq("market", result["market"]).execute()

    logger.info("qualification step2: wrote %d results", len(enriched))
    return {"status": "ok", "processed": len(enriched)}


# ── Steps 3 + 4 stubs (built next session) ───────────────────────────────────

async def run_step3() -> dict:
    # ⚠️ PENDING: Brevo CRM API spec
    raise NotImplementedError("Step 3 not yet implemented")


async def run_step4() -> dict:
    # ⚠️ PENDING: qualification rules to be defined
    raise NotImplementedError("Step 4 not yet implemented")


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/pipelines/qualify")
async def run_qualification():
    """Runs Step 2 (technographic). Steps 3 + 4 added in next session."""
    return await run_step2()
