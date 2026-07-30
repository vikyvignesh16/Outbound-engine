"""Personalised ABM landing page generator.

Calls the external page-generation API at
https://web-production-a4433.up.railway.app/generate to mint a per-company
landing page for the Email 1 LP teaser anchor. The API is slow (35-45s per
call) and idempotent per company, so we cache one row per domain forever
in company_lp_cache. Subsequent contacts at the same company reuse the URL.

2026-07-28: payload expanded to the "create_abm1" schema — the API now
takes archetype (required, drives the whole page) and market (routes the
final CTA) as structured routing fields, plus a set of enrichment signals
(icp_archetype_evidence, account_fit_reasoning, esp_detected/score,
has_loyalty_program, has_wallet, needs_cdp, email_crm_activity) that the
LP-side writer uses as context — these are never printed verbatim on the
page, they just shape what it writes. `title` is the page/browser-tab
title (company-level, e.g. "Nautica x Brevo"), not the contact's job
title — the page stays one-per-domain, reused across every contact at
that company, same as before.

Markets are mapped from our internal codes (UK / Ireland / DE / AT / CH / US
/ FR) to the API's lowercase enum (uki / dach / us / fr). Archetypes are
mapped from our Title Case names (Graduate, Network, ...) to the API's
snake_case enum (graduate, network, ...) — a missing/unclassified archetype
is sent as the literal string "none" rather than skipping the call or
guessing a default, per an explicit decision to always attempt an LP.

Flow per domain:
  1. Look up company_lp_cache.
  2. Hit → return cached preview_url.
  3. Miss → POST to /generate with the full create_abm1 payload. Cache the
     result (success or already_existed). Return the URL.
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

# Per-call timeout. Docs recommend 90s+ given LLM gen + Brevo Pages publish.
# Bumped from 120s to 180s after observing ~5 stubborn domains (large /
# complex companies) whose generation reliably runs past 120s and then 502s.
_TIMEOUT_S = 180.0

# Map our market codes to the API's market enum (routes the final CTA
# round-robin) and to the page's written language.
#
# Confirmed live 2026-07-28 (direct probe against the API): it only accepts
# market as UPPERCASE 'UKI' | 'DACH' | 'USA' | 'FR' — the lowercase
# dach/uki/us/fr enum we were originally told about 422s. FR was added to
# the live schema and end-to-end verified the same day (real preview_url
# returned for a test FR company) after the Railway service running this
# API was redeployed with the FR-enabled source.
_MARKET_SLUG: dict[str, str] = {
    "UK": "UKI", "Ireland": "UKI", "IE": "UKI",
    "DE": "DACH", "AT": "DACH", "CH": "DACH",
    "US": "USA",
    "FR": "FR", "France": "FR",
}
# Slug -> lang directly, since _mint() only has the already-normalised slug
# on hand by the time it needs to pick a language.
_SLUG_LANG: dict[str, str] = {"UKI": "en", "DACH": "de", "USA": "en", "FR": "fr"}

# Map our Title Case archetype names (as stored on priority_tam /
# icp_archetype_primary) to the API's required snake_case enum.
_ARCHETYPE_SLUG: dict[str, str] = {
    "Graduate":           "graduate",
    "Network":            "network",
    "Consolidator":       "consolidator",
    "Email Specialist":   "email_specialist",
    "Feature Specialist": "feature_specialist",
    "Saver":              "saver",
}


def _normalise_market(market: str | None) -> str | None:
    if not market:
        return None
    return _MARKET_SLUG.get(market.strip())


def _archetype_slug(archetype: str | None) -> str:
    """"None"/empty/unrecognised all become the literal string "none" — sent
    as-is rather than skipping the LP call or guessing a fallback archetype,
    per explicit decision (2026-07-28)."""
    if not archetype:
        return "none"
    return _ARCHETYPE_SLUG.get(archetype.strip(), "none")


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
    archetype: str,
    icp_archetype_secondary: str | None = None,
    icp_archetype_evidence: str | None = None,
    account_fit_reasoning: str | None = None,
    account_fit_score: int | None = None,
    esp_score: int | None = None,
    has_loyalty_program: bool | None = None,
    has_wallet: bool | None = None,
    needs_cdp: bool | None = None,
    email_crm_activity: str | None = None,
    logo_url: str | None = None,
) -> dict | None:
    """Single POST to the LP generator. Returns the parsed response dict on
    success, None on error (so caller can decide whether to skip the contact
    or fall back).

    `market`/`archetype` here are already the API's slugs (lowercase /
    snake_case) — callers pass the normalised values, this function just
    assembles and sends the body.
    """
    body = {
        "company":        company_name,
        "title":          f"{company_name} x Brevo",
        # The live API 422s with "domain: Field required" if this bare key is
        # missing — confirmed 2026-07-28 (every fresh mint failed until this
        # was added). Sent alongside company_domain since the schema we were
        # given explicitly names that one too (logo.dev + contact-card email).
        "domain":         domain,
        "company_domain": domain,
        "lang":           _SLUG_LANG.get(market, "en"),
        "industry":       industry,
        "vertical":       industry,
        "archetype":      archetype,
        "market":         market,
    }
    if logo_url:
        body["logo_url"] = logo_url

    # Enrichment signals — context for the LP-side writer, never printed
    # verbatim on the page. Omitted when we simply don't have the value
    # rather than sending null/empty-string noise.
    if icp_archetype_secondary:
        body["icp_archetype_secondary"] = icp_archetype_secondary
    if icp_archetype_evidence:
        body["icp_archetype_evidence"] = icp_archetype_evidence
    if account_fit_reasoning:
        body["account_fit_reasoning"] = account_fit_reasoning
    if account_fit_score is not None:
        body["account_fit_score"] = account_fit_score
    if esp:
        body["esp_detected"] = esp
    if esp_score is not None:
        body["esp_score"] = esp_score
    if has_loyalty_program is not None:
        body["has_loyalty_program"] = has_loyalty_program
    if has_wallet is not None:
        body["has_wallet"] = has_wallet
    if needs_cdp is not None:
        body["needs_cdp"] = needs_cdp
    if email_crm_activity:
        body["email_crm_activity"] = email_crm_activity

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
    icp_archetype_primary: str | None = None,
    icp_archetype_secondary: str | None = None,
    icp_archetype_evidence: str | None = None,
    account_fit_reasoning: str | None = None,
    account_fit_score: int | None = None,
    esp_score: int | None = None,
    has_loyalty_program: bool | None = None,
    has_wallet: bool | None = None,
    needs_cdp: bool | None = None,
    email_crm_activity: str | None = None,
    logo_url: str | None = None,
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
        archetype=_archetype_slug(icp_archetype_primary),
        icp_archetype_secondary=icp_archetype_secondary,
        icp_archetype_evidence=icp_archetype_evidence,
        account_fit_reasoning=account_fit_reasoning,
        account_fit_score=account_fit_score,
        esp_score=esp_score,
        has_loyalty_program=has_loyalty_program,
        has_wallet=has_wallet,
        needs_cdp=needs_cdp,
        email_crm_activity=email_crm_activity,
        logo_url=logo_url,
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

    Input items: {domain, company_name, industry, market, esp_detected,
    esp_score, icp_archetype_primary, icp_archetype_secondary,
    icp_archetype_evidence, account_fit_reasoning, account_fit_score,
    has_loyalty_program, has_wallet, needs_cdp, email_crm_activity}.
    Returns {domain -> preview_url}. Missing/failed lookups are silently
    omitted from the result so callers can `.get(domain, "")` safely.
    """
    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    out: dict[str, str] = {}

    async def _one(item: dict) -> None:
        async with sem:
            url = await fetch_company_lp(
                domain                  = item.get("domain") or "",
                company_name            = item.get("company_name") or "",
                industry                = item.get("industry"),
                market                  = item.get("market"),
                esp                     = item.get("esp_detected"),
                icp_archetype_primary   = item.get("icp_archetype_primary"),
                icp_archetype_secondary = item.get("icp_archetype_secondary"),
                icp_archetype_evidence  = item.get("icp_archetype_evidence"),
                account_fit_reasoning   = item.get("account_fit_reasoning"),
                account_fit_score       = item.get("account_fit_score"),
                esp_score               = item.get("esp_score"),
                has_loyalty_program     = item.get("has_loyalty_program"),
                has_wallet              = item.get("has_wallet"),
                needs_cdp               = item.get("needs_cdp"),
                email_crm_activity      = item.get("email_crm_activity"),
                logo_url                = item.get("logo_url"),
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
