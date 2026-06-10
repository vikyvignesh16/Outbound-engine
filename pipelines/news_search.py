"""Per-company news search for the Email 1 "I came across..." opener.

The content generation pipeline (pipelines/content.py) needs a recent-news
hook for each contact's company. We do it once per domain and cache the
result indefinitely — manual DELETE on company_news_cache to refresh.

Flow per domain:
  1. Look up company_news_cache by domain.
  2. Hit → return cached row (no API call).
  3. Miss → call Anthropic Messages with web_search tool, parse the JSON
     payload Claude returns, persist to cache, return it.
  4. On API error → log and return a "no news" result without caching, so
     the next batch retries.

Result shape:
  {found: bool, usable: bool, news_summary: str, news_type: str}

The prompt below is the "Part 1 — News Search Prompt" from the master
content spec. It scopes the search to 2025-2026 strategic news that has a
natural bridge to customer communications.
"""
import asyncio
import json
import logging
import os
import re
from datetime import date

import anthropic

from db.client import get_supabase

logger = logging.getLogger(__name__)

# Concurrency cap for the per-domain fan-out at the start of a content batch.
_MAX_INFLIGHT = 25

# Model used for the news search step. Sonnet is overkill for a single
# JSON-out call after a web search; haiku is faster and cheaper.
_MODEL = "claude-haiku-4-5"

_PROMPT_TEMPLATE = """Search for recent news about "{company_name}" published in 2025 or 2026 only. Today is {today}.

We are looking for news that has a DIRECT, OBVIOUS connection to how this company communicates with its customers. We sell email marketing, SMS, CRM, marketing automation, loyalty programmes, and mobile wallet products. The news must give us a natural reason to reach out about one of those things.

ONLY return news that fits one of these specific categories:
- Launching, redesigning, expanding, or changing a loyalty or rewards programme
- Investing in or replacing an email marketing, SMS, CRM, or marketing automation platform
- Mobile app launches or major updates focused on customer engagement (not store-locator or operational apps)
- Mobile wallet integrations (Apple Wallet, Google Wallet, digital card launches)
- Hiring a Head/VP/Director of CRM, Customer Marketing, Lifecycle, or Customer Experience
- Public statements about changing how they talk to or engage their customers across channels

REJECT all of these, even if they sound interesting or recent:
- Store openings, branch expansion, location milestones
- Partnerships with POS, payments, inventory, AI, retail-tech, or operations vendors (unless explicitly about customer email/loyalty/CRM)
- Delivery partnerships or logistics announcements
- Generic "digital transformation", "AI rollout", or "in-store technology" announcements
- Product range changes, menu updates, new SKUs
- Sponsorships, awards, CSR, environmental announcements
- Financial results, M&A, executive hires outside CRM/marketing
- Brand campaigns, advertising launches, sponsorships
- Anything generic enough it could apply to any company in the sector

If there is no news that fits the strict categories above, set found = false. It is better to have no news than to force a connection that does not exist.

Return ONLY this JSON, no preamble, no markdown:
{{
  "found": true or false,
  "news_summary": "one sentence describing the news in plain English, or empty string",
  "news_type": "loyalty|email|crm|martech|app|wallet|hire|customer_comms or empty string",
  "usable": true ONLY if there is a clear, specific connection to email marketing, loyalty programmes, CRM, customer communications, or wallet. False otherwise.
}}"""


_NO_NEWS = {
    "found": False,
    "usable": False,
    "news_summary": "",
    "news_type": "",
}


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(text: str) -> dict | None:
    """Pull the JSON object out of the model's final text response.

    Claude can wrap JSON in markdown fences or prefix it with stray prose
    even when told not to; extract from the outermost {...} block.
    """
    if not text:
        return None
    if "```" in text:
        # Strip markdown fences
        text = text.split("```", 1)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        logger.warning("news_search: failed to parse JSON: %s — text was: %r", exc, text[:200])
        return None


def _final_text(message) -> str:
    """Return the last text content block from a Messages response."""
    for block in reversed(message.content):
        if getattr(block, "type", None) == "text":
            return block.text or ""
    return ""


async def _fetch_one(domain: str, company_name: str) -> dict:
    """Hit Anthropic web_search for a single domain. Returns the parsed JSON
    result, or the _NO_NEWS shape on any failure."""
    prompt = _PROMPT_TEMPLATE.format(
        company_name=company_name or domain,
        today=date.today().strftime("%d/%m/%Y"),
    )
    try:
        client = _get_client()
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
            }],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        logger.exception("news_search: API call failed for %s: %s", domain, exc)
        return _NO_NEWS  # uncached → retry next batch

    parsed = _extract_json(_final_text(message))
    if not parsed:
        # Treat unparseable as "no news"; cache so we don't burn another search.
        return {**_NO_NEWS, "raw": {"final_text": _final_text(message)[:1000]}}

    return {
        "found":        bool(parsed.get("found")),
        "usable":       bool(parsed.get("usable")),
        "news_summary": (parsed.get("news_summary") or "").strip(),
        "news_type":    (parsed.get("news_type") or "").strip(),
        "raw":          parsed,
    }


def _cached(domain: str) -> dict | None:
    sb = get_supabase()
    rows = (
        sb.table("company_news_cache")
        .select("domain,found,usable,news_summary,news_type")
        .eq("domain", domain)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def _persist(domain: str, result: dict) -> None:
    sb = get_supabase()
    raw = result.pop("raw", None)
    sb.table("company_news_cache").upsert({
        "domain":       domain,
        "found":        result["found"],
        "usable":       result["usable"],
        "news_summary": result["news_summary"],
        "news_type":    result["news_type"],
        "raw":          raw,
    }, on_conflict="domain").execute()


async def fetch_company_news(domain: str, company_name: str = "") -> dict:
    """Cache-first single-domain lookup. Returns {found, usable, news_summary, news_type}.

    Failures don't write to cache (retry next batch). Successful "no news"
    results DO write to cache to avoid re-paying for the same null answer.
    """
    domain = (domain or "").strip().lower()
    if not domain:
        return _NO_NEWS

    hit = _cached(domain)
    if hit is not None:
        return {
            "found":        hit["found"],
            "usable":       hit["usable"],
            "news_summary": hit.get("news_summary") or "",
            "news_type":    hit.get("news_type") or "",
        }

    result = await _fetch_one(domain, company_name)
    if result is _NO_NEWS:
        # API error → don't cache, return as-is so a retry can re-attempt
        return _NO_NEWS

    try:
        _persist(domain, dict(result))
    except Exception:
        logger.exception("news_search: failed to persist cache for %s", domain)

    # _persist popped 'raw' off the dict; remove it from the return shape too
    result.pop("raw", None)
    return result


async def fetch_many(domains_with_names: list[tuple[str, str]]) -> dict[str, dict]:
    """Fan out fetch_company_news across many (domain, company_name) pairs
    with bounded concurrency. Returns {domain -> news dict}."""
    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    seen: dict[str, dict] = {}

    async def _one(domain: str, name: str) -> None:
        async with sem:
            seen[domain] = await fetch_company_news(domain, name)

    # Dedupe — same domain only fetched once even if it appears multiple times
    unique: dict[str, str] = {}
    for domain, name in domains_with_names:
        d = (domain or "").strip().lower()
        if d and d not in unique:
            unique[d] = name or ""

    await asyncio.gather(*[_one(d, n) for d, n in unique.items()])
    return seen
