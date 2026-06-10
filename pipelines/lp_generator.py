"""Personalised ABM landing page generator.

Calls the external page-generation API at
https://web-production-a4433.up.railway.app/generate to mint a per-company
landing page for the Email 1 LP teaser anchor. The API is slow (35-45s per
call) and idempotent per company, so we cache one row per domain forever
in company_lp_cache. Subsequent contacts at the same company reuse the URL.

Markets are mapped from our internal codes (UK / Ireland / DE / AT / CH / US)
to the API's enum (UKI / DACH / USA).

Flow per domain:
  1. Look up company_lp_cache.
  2. Hit → return cached preview_url.
  3. Miss → POST to /generate with company + domain + industry + market (+ esp).
     Cache the result (success or already_existed). Return the URL.
  4. On HTTP/validation/network error → log, return None, do NOT cache so
     the next batch retries.
"""
import asyncio
import logging
import os

import httpx

from db.client import get_supabase

logger = logging.getLogger(__name__)

_API_URL = os.environ.get(
    "LP_GENERATOR_URL",
    "https://web-production-a4433.up.railway.app/generate",
)

# Concurrency cap. Per-call latency is ~35-45s so 293 companies serial would
# be 3-4 hours; with 15 in-flight, ~12 min wall-clock for batch 1.
_MAX_INFLIGHT = 15

# Per-call timeout — docs recommend 90s+ given LLM gen + Brevo Pages publish.
_TIMEOUT_S = 120.0

# Map our market codes to the API's enum.
_MARKET_MAP: dict[str, str] = {
    "UK":      "UKI",
    "Ireland": "UKI",
    "IE":      "UKI",
    "DE":      "DACH",
    "AT":      "DACH",
    "CH":      "DACH",
    "US":      "USA",
}


def _normalise_market(market: str | None) -> str | None:
    if not market:
        return None
    return _MARKET_MAP.get(market.strip())


def _normalise_esp(esp: str | None) -> str | None:
    """Skip ESP if missing or 'unknown' so the API doesn't get junk values."""
    if not esp:
        return None
    e = esp.strip()
    if not e or e.lower() in {"unknown", "none", "n/a"}:
        return None
    return e


def _cached(domain: str) -> dict | None:
    sb = get_supabase()
    rows = (
        sb.table("company_lp_cache")
        .select("domain,preview_url,slug,market,already_existed")
        .eq("domain", domain)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def _persist(domain: str, payload: dict) -> None:
    sb = get_supabase()
    sb.table("company_lp_cache").upsert({
        "domain":          domain,
        "preview_url":     payload["preview_url"],
        "slug":            payload.get("slug"),
        "market":          payload.get("_market"),
        "already_existed": payload.get("already_exists"),
        "raw":             {k: v for k, v in payload.items() if k != "_market"},
    }, on_conflict="domain").execute()


async def _mint(
    domain: str,
    company_name: str,
    industry: str,
    market: str,
    esp: str | None,
) -> dict | None:
    """Single POST to the LP generator. Returns the parsed response dict on
    success, None on error (so caller can decide whether to skip the contact
    or fall back)."""
    body = {
        "company":  company_name,
        "domain":   domain,
        "industry": industry,
        "market":   market,
    }
    if esp:
        body["esp"] = esp

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            r = await client.post(_API_URL, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        # 422 = validation; 502 = upstream Brevo Pages error. Don't cache.
        logger.warning(
            "lp_generator: %s for %s — status=%s body=%s",
            type(exc).__name__, domain, exc.response.status_code,
            (exc.response.text or "")[:300],
        )
        return None
    except Exception:
        logger.exception("lp_generator: unexpected error for %s", domain)
        return None

    if not data.get("preview_url"):
        logger.warning(
            "lp_generator: response for %s had no preview_url — %s",
            domain, str(data)[:300],
        )
        return None

    data["_market"] = market
    return data


async def fetch_company_lp(
    domain: str,
    company_name: str,
    industry: str | None,
    market: str | None,
    esp: str | None = None,
) -> str | None:
    """Cache-first lookup. Returns the preview_url or None on missing inputs
    or unrecoverable error. None means "we couldn't get a URL for this
    contact" — caller should treat that as a soft fail (skip the LP teaser
    anchor for this contact) rather than failing the batch.
    """
    domain = (domain or "").strip().lower()
    if not domain:
        return None

    hit = _cached(domain)
    if hit:
        return hit["preview_url"]

    api_market = _normalise_market(market)
    industry = (industry or "").strip()
    company_name = (company_name or "").strip() or domain
    if not api_market:
        logger.info(
            "lp_generator: skipping %s — unmapped market %r", domain, market,
        )
        return None
    if not industry:
        logger.info(
            "lp_generator: skipping %s — no industry/vertical available", domain,
        )
        return None

    payload = await _mint(
        domain,
        company_name=company_name,
        industry=industry,
        market=api_market,
        esp=_normalise_esp(esp),
    )
    if not payload:
        return None

    try:
        _persist(domain, payload)
    except Exception:
        logger.exception("lp_generator: persist failed for %s", domain)

    return payload["preview_url"]


async def fetch_many(companies: list[dict]) -> dict[str, str]:
    """Fan out fetch_company_lp across many companies with bounded concurrency.

    Input items: {domain, company_name, industry, market, esp}.
    Returns {domain -> preview_url}. Missing/failed lookups are silently
    omitted from the result so callers can `.get(domain, "")` safely.
    """
    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    out: dict[str, str] = {}

    async def _one(item: dict) -> None:
        async with sem:
            url = await fetch_company_lp(
                domain       = item.get("domain") or "",
                company_name = item.get("company_name") or "",
                industry     = item.get("industry"),
                market       = item.get("market"),
                esp          = item.get("esp"),
            )
            if url:
                out[(item.get("domain") or "").strip().lower()] = url

    # Dedupe by domain — same domain only minted once even if appears in
    # the input multiple times
    unique: dict[str, dict] = {}
    for c in companies:
        d = (c.get("domain") or "").strip().lower()
        if d and d not in unique:
            unique[d] = c

    await asyncio.gather(*[_one(c) for c in unique.values()])
    return out
