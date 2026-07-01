"""Recover the correct LinkedIn company page for contact_gaps rows whose
sourced_tam_v2.linkedin_url turned out to be dead / unclaimed / points to
the wrong entity.

Trigger — a contact_gaps row lands here when poll_phase1 sees PB Company
Extractor return zero result rows. Historically these were dead-lettered
as gap_reason='no_company_id_returned' and left for manual cleanup;
2026-07-01 we discovered ~76% of the UK gifting batch #2 gaps failed this
way (all traceable to bad LinkedIn URLs in sourced_tam_v2 that Clay's
enrichment attached at qualification time).

This pipeline uses Claude Haiku 4.5 + web_search to find the company's
real primary LinkedIn page, constrained to the given market. On success:
updates sourced_tam_v2.linkedin_url in-place AND resets the contact_gaps
row to 'pending' so poll_phase1 retries with the corrected URL. On
failure: archives the row to contact_gaps_failed with gap_reason
'linkedin_url_not_recoverable'.

Runs as its own Railway cron (every 30 min) hitting
POST /pipelines/recover-linkedin-urls — kept separate from the tight
5-minute contact-gaps poll cadence so the ~5-10 second Claude call per
row doesn't slow that hot loop.
"""
import asyncio
import logging
import os
import re

import anthropic
from fastapi import APIRouter, BackgroundTasks

from db.client import fetch_all, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

_MODEL = "claude-haiku-4-5"
_MAX_INFLIGHT = 5
_MAX_TOKENS = 2048
_MAX_WEB_SEARCH_USES = 3

# Only /company/{slug} URLs — reject /in/ (personal), /learning/, /pulse/, /jobs/
_LINKEDIN_COMPANY_URL_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9._&%\-]+/?",
    re.IGNORECASE,
)


_SYSTEM_PROMPT = """You are a data recovery specialist. For a given company name,
market, and website, find the OFFICIAL LinkedIn company page.

RULES:
- Use the web_search tool to look up. Do not guess based on memory.
- Prefer the parent / HQ page over a subsidiary or single-location page
  (e.g. prefer "Hilton Worldwide" over "Hilton Paris").
- The company must operate in the given market — verify from LinkedIn's
  "About" section, headquartered field, or employee location distribution.
- Return the canonical URL of the form
  https://www.linkedin.com/company/{slug}
- If no verifiable primary page exists (defunct, acquired, no LinkedIn
  presence), return exactly: NOT_FOUND
- Do NOT return search result URLs, LinkedIn Learning URLs, profile URLs
  (/in/...), pulse articles, or job posting URLs — only /company/... pages.

Respond with a single line: either the URL, or the literal string NOT_FOUND.
Do not add prose, quotes, or markdown.
"""


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_url(text: str) -> str | None:
    """Pull the first /company/ LinkedIn URL from Claude's response."""
    if not text:
        return None
    if "NOT_FOUND" in text.upper():
        return None
    m = _LINKEDIN_COMPANY_URL_RE.search(text)
    if not m:
        return None
    return m.group(0).rstrip("/")


async def find_linkedin_url(
    client: anthropic.AsyncAnthropic,
    company_name: str,
    market: str,
    domain: str,
) -> str | None:
    """Single Claude call to look up the correct LinkedIn company URL."""
    user = (
        f"Company name: {company_name}\n"
        f"Market:       {market}\n"
        f"Website:      {domain}\n\n"
        f"Find the official LinkedIn company page."
    )
    tools = [{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": _MAX_WEB_SEARCH_USES,
    }]
    try:
        msg = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            tools=tools,
            messages=[{"role": "user", "content": user}],
        )
    except Exception:
        logger.exception("linkedin_url_recovery: Claude call failed for %s", company_name)
        return None

    # Grab the final text response (after any web_search tool use)
    text_parts = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)
    combined = "\n".join(text_parts).strip()
    return _extract_url(combined)


def _normalise_linkedin(url: str | None) -> str:
    if not url:
        return ""
    u = url.strip().lower().rstrip("/")
    for prefix in ("https://", "http://"):
        if u.startswith(prefix):
            u = u[len(prefix):]
            break
    if u.startswith("www."):
        u = u[4:]
    return u


async def _process_one(
    client: anthropic.AsyncAnthropic,
    row: dict,
    sem: asyncio.Semaphore,
) -> dict:
    async with sem:
        new_url = await find_linkedin_url(
            client, row["company_name"], row["market"] or "", row["domain"]
        )
        sb = get_supabase()

        # What URL does sourced_tam_v2 currently have? If Claude returns the
        # SAME URL that already failed PB, retrying will just fail again —
        # archive instead of looping.
        current = sb.table("sourced_tam_v2").select("linkedin_url").eq(
            "domain", row["domain"]
        ).order("updated_at", desc=True).limit(1).execute().data
        current_url = (current[0]["linkedin_url"] if current else "") or ""

        if new_url and _normalise_linkedin(new_url) == _normalise_linkedin(current_url):
            logger.info("linkedin_url_recovery: %s — Claude returned same URL that already failed, archiving",
                        row["domain"])
            new_url = None  # fall through to archive branch

        if new_url:
            # Update every sourced_tam_v2 row for this domain (Clay may have
            # multiple with different LinkedIn URLs — the ONE we search on for
            # PB Phase 1 is picked by ORDER BY updated_at DESC, so touching
            # them all guarantees the next launch uses the recovered URL).
            try:
                sb.table("sourced_tam_v2").update({
                    "linkedin_url": new_url
                }).eq("domain", row["domain"]).execute()
                sb.table("contact_gaps").update({
                    "phantombuster_status": "pending",
                    "gap_reason":           "no_contacts",   # reset to normal
                    "phantom_id":           None,
                }).eq("id", row["id"]).execute()
                logger.info("linkedin_url_recovery: recovered %s → %s",
                            row["domain"], new_url)
                return {"domain": row["domain"], "outcome": "recovered", "url": new_url}
            except Exception:
                logger.exception("linkedin_url_recovery: DB update failed for %s", row["domain"])
                return {"domain": row["domain"], "outcome": "db_error"}

        # No URL found — archive to contact_gaps_failed and remove from active queue
        try:
            full_row = sb.table("contact_gaps").select("*").eq("id", row["id"]).execute().data
            if full_row:
                archive_row = {**full_row[0], "gap_reason": "linkedin_url_not_recoverable"}
                sb.table("contact_gaps_failed").insert(archive_row).execute()
                sb.table("contact_gaps").delete().eq("id", row["id"]).execute()
            logger.info("linkedin_url_recovery: not recoverable %s (archived)", row["domain"])
            return {"domain": row["domain"], "outcome": "archived"}
        except Exception:
            logger.exception("linkedin_url_recovery: archive failed for %s", row["domain"])
            return {"domain": row["domain"], "outcome": "archive_error"}


async def run_linkedin_url_recovery(limit: int | None = None) -> dict:
    """Process contact_gaps rows where phantombuster_status='failed' and
    gap_reason='linkedin_url_dead'. Returns per-outcome counts + samples."""
    rows = fetch_all(
        "contact_gaps",
        "id, domain, company_name, market, batch_number, phantom_id",
        filters=[
            ("eq", "phantombuster_status", "failed"),
            ("eq", "gap_reason", "linkedin_url_dead"),
        ],
        limit=limit,
    )
    if not rows:
        logger.info("linkedin_url_recovery: nothing to do")
        return {"status": "ok", "processed": 0}

    logger.info("linkedin_url_recovery: %d rows to process", len(rows))
    client = _client()
    sem = asyncio.Semaphore(_MAX_INFLIGHT)

    results = await asyncio.gather(*[_process_one(client, r, sem) for r in rows])
    by_outcome: dict[str, int] = {}
    for r in results:
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1

    sample_recovered = [r for r in results if r["outcome"] == "recovered"][:10]
    sample_archived = [r for r in results if r["outcome"] == "archived"][:10]

    logger.info("linkedin_url_recovery: done — %s", by_outcome)
    return {
        "status":            "ok",
        "processed":         len(rows),
        "by_outcome":        by_outcome,
        "sample_recovered":  sample_recovered,
        "sample_archived":   sample_archived,
    }


@router.post("/pipelines/recover-linkedin-urls")
async def recover_linkedin_urls(background_tasks: BackgroundTasks, limit: int | None = None):
    """Cron-friendly (every 30 min). Runs in background so the caller returns
    fast; the Claude calls take ~5-10 seconds per row."""
    async def _run():
        await run_linkedin_url_recovery(limit=limit)
    background_tasks.add_task(_run)
    return {"status": "accepted", "background": True, "limit": limit}
