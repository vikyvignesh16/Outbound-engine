"""Domain Quality Agent — Claude Haiku 4.5 + web_search loop over qualified_tam_v2.

Runs every 6 hours via Railway cron on rows where domain_quality_checked_at IS NULL.
Each row gets its own agent loop (concurrency 5). For each row, the agent decides:

  1. Is the domain bogus? (job board, careers portal, gov service, social media, ATS)
  2. If bogus, what is the company's real primary website? (web_search)
  3. Is the domain shared with sibling companies in our TAM?
       - Related sibling names (Hilton Berlin / Hilton Munich on hilton.com) → chain brand
       - Unrelated sibling names (Bakers + Baristas / Bord Gáis on allens.ie) → bogus
  4. For chain brands: is THIS row a Regional/Country HQ (keep + contact) or a
     property/branch/franchisee (flag + skip — head office gets contacted)?

Skills exposed to the agent:
  - detect_bogus_pattern        (custom) — pure-regex bogus detector
  - find_companies_sharing_domain (custom) — DB query for siblings
  - web_search                  (native Anthropic tool) — verify correct domain / parent identity
  - save_verdict                (custom) — persist verdict, ends the loop

Verdict columns written to qualified_tam_v2:
  domain_status:             verified | bogus | subsidiary | corrected
  domain_role:               regional_hq | country_hq | global_hq | property |
                             branch | franchisee | independent
  parent_company_name:       the head-office entity (for subsidiary rows)
  domain_corrected_to:       the new domain (when status='corrected')
  domain_quality_checked_at: NOW() — set on every save_verdict call so the 6h cron
                             can skip already-checked rows
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks

from db.client import fetch_all, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

_MODEL = "claude-haiku-4-5"
_MAX_INFLIGHT = 5
_MAX_TURNS = 8       # safety cap on agent loop iterations per row
_MAX_TOKENS = 4096
_MAX_WEB_SEARCH_USES = 3


# ── Skill 1: detect_bogus_pattern ────────────────────────────────────────────

_BOGUS_PATTERNS = [
    (re.compile(r"\.jobs($|/)",                                                    re.I), "TLD .jobs — job board"),
    (re.compile(r"^careers?\.",                                                    re.I), "subdomain careers/career"),
    (re.compile(r"^jobs\.",                                                        re.I), "subdomain jobs"),
    (re.compile(r"careers\.com$|careers\.co\.uk$",                                 re.I), "careers domain"),
    (re.compile(r"\.gov\.|\.gov$",                                                 re.I), "government domain"),
    (re.compile(r"linkedin\.com|facebook\.com|twitter\.com|instagram\.com|x\.com|tiktok\.com|youtube\.com", re.I), "social media platform"),
    (re.compile(r"workable\.com|lever\.co|greenhouse\.io|smartrecruiters\.com|bamboohr\.com|jobylon\.com|teamtailor\.com|workday\.com", re.I), "applicant tracking system"),
    (re.compile(r"indeed\.com|glassdoor\.com|monster\.com|reed\.co\.uk|totaljobs\.com", re.I), "job aggregator"),
    (re.compile(r"hrewards\.com|loyalty\.",                                        re.I), "loyalty / rewards portal"),
]


def _skill_detect_bogus_pattern(domain: str) -> dict:
    if not domain:
        return {"is_bogus": False, "reason": "empty domain"}
    for pat, reason in _BOGUS_PATTERNS:
        if pat.search(domain):
            return {"is_bogus": True, "reason": reason, "matched_pattern": pat.pattern}
    return {"is_bogus": False, "reason": "no bogus pattern matched"}


# ── Skill 2: find_companies_sharing_domain ───────────────────────────────────

def _skill_find_companies_sharing_domain(domain: str, exclude_id: str | None = None) -> dict:
    if not domain:
        return {"count": 0, "companies": []}
    sb = get_supabase()
    found: list[dict] = []
    for table in ("qualified_tam_v2", "priority_tam", "priority_tam_parked"):
        try:
            rows = sb.table(table).select("id, company_name, market").eq("domain", domain).execute().data or []
        except Exception:
            rows = []
        for r in rows:
            if exclude_id and r.get("id") == exclude_id:
                continue
            found.append({"company_name": r.get("company_name"), "market": r.get("market")})
    # Dedupe by (company_name, market)
    seen, deduped = set(), []
    for r in found:
        key = (r["company_name"], r["market"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return {"count": len(deduped), "companies": deduped[:60]}


# ── Skill 3: save_verdict ────────────────────────────────────────────────────

def _skill_save_verdict(
    row_id: str,
    domain_status: str,
    domain_role: str | None = None,
    parent_company_name: str | None = None,
    domain_corrected_to: str | None = None,
) -> dict:
    update = {
        "domain_status": domain_status,
        "domain_quality_checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if domain_role:
        update["domain_role"] = domain_role
    if parent_company_name:
        update["parent_company_name"] = parent_company_name
    if domain_corrected_to:
        # Record what the agent found, and ATTEMPT to swap the domain in place.
        # If the new domain collides with an existing (domain, market, company_name)
        # row, fall back to recording-only — downstream code should use
        # COALESCE(domain_corrected_to, domain).
        update["domain_corrected_to"] = domain_corrected_to
        update["domain"] = domain_corrected_to
    sb = get_supabase()
    try:
        sb.table("qualified_tam_v2").update(update).eq("id", row_id).execute()
        return {"ok": True, "wrote": list(update.keys()), "domain_swapped": bool(domain_corrected_to)}
    except Exception as exc:
        # Unique-constraint conflict on (domain, market, company_name) when swapping —
        # retry without the in-place domain swap (still record domain_corrected_to).
        if domain_corrected_to and "duplicate key" in str(exc).lower():
            logger.warning(
                "save_verdict: duplicate (domain,market,name) for row %s — "
                "recording domain_corrected_to=%s without in-place swap",
                row_id, domain_corrected_to,
            )
            update.pop("domain", None)
            try:
                sb.table("qualified_tam_v2").update(update).eq("id", row_id).execute()
                return {"ok": True, "wrote": list(update.keys()),
                        "domain_swapped": False, "note": "duplicate prevented swap"}
            except Exception as exc2:
                logger.exception("save_verdict: fallback also failed for %s", row_id)
                return {"ok": False, "error": str(exc2)[:200]}
        logger.exception("save_verdict: failed for row %s", row_id)
        return {"ok": False, "error": str(exc)[:200]}


# ── Tool schemas + dispatcher ────────────────────────────────────────────────

_CUSTOM_TOOLS = {
    "detect_bogus_pattern":          _skill_detect_bogus_pattern,
    "find_companies_sharing_domain": _skill_find_companies_sharing_domain,
    "save_verdict":                  _skill_save_verdict,
}

_TOOL_SCHEMAS = [
    {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": _MAX_WEB_SEARCH_USES,
    },
    {
        "name": "detect_bogus_pattern",
        "description": (
            "Cheap regex check — does the domain match known-bogus patterns? "
            "Patterns include: TLD .jobs, subdomains careers./jobs., government "
            "domains (.gov.*), social media (linkedin/facebook/etc), applicant "
            "tracking systems (workable, greenhouse, lever), job aggregators "
            "(indeed, glassdoor), loyalty portals (hrewards). Returns "
            "is_bogus + reason. ALWAYS call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"domain": {"type": "string"}},
            "required": ["domain"],
        },
    },
    {
        "name": "find_companies_sharing_domain",
        "description": (
            "Query our TAM tables (qualified_tam_v2 + priority_tam + parked) for "
            "all OTHER companies on this same domain. Returns count + up to 60 "
            "sibling company names. Critical signal: many UNRELATED names on the "
            "same domain → bogus shared domain. Many RELATED names (Hilton X, "
            "Hilton Y) → legitimate chain brand. ALWAYS pass exclude_id with the "
            "current row's id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain":     {"type": "string"},
                "exclude_id": {"type": "string", "description": "The current row's id (UUID) to exclude from siblings."},
            },
            "required": ["domain"],
        },
    },
    {
        "name": "save_verdict",
        "description": (
            "Persist the final verdict to qualified_tam_v2 and end this loop. "
            "domain_status (required): 'verified' (independent, valid unique domain), "
            "'bogus' (couldn't recover a real domain), 'subsidiary' (this row shares "
            "a domain with a parent — DO NOT contact directly), 'corrected' (we found "
            "and replaced a bogus domain — supply domain_corrected_to). "
            "domain_role: 'regional_hq' / 'country_hq' / 'global_hq' (KEEP, contactable), "
            "'property' / 'branch' / 'franchisee' (FLAG, do not contact), 'independent'. "
            "parent_company_name: the head-office name (when subsidiary). "
            "domain_corrected_to: the new correct domain (when status='corrected')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "row_id":              {"type": "string"},
                "domain_status":       {"type": "string", "enum": ["verified", "bogus", "subsidiary", "corrected"]},
                "domain_role":         {"type": "string", "enum": ["regional_hq", "country_hq", "global_hq", "property", "branch", "franchisee", "independent"]},
                "parent_company_name": {"type": "string"},
                "domain_corrected_to": {"type": "string"},
            },
            "required": ["row_id", "domain_status"],
        },
    },
]


def _execute_custom_tool(name: str, input_args: dict) -> dict:
    fn = _CUSTOM_TOOLS.get(name)
    if not fn:
        return {"error": f"unknown tool: {name}"}
    try:
        return fn(**input_args)
    except Exception as exc:
        logger.exception("custom tool %s failed", name)
        return {"error": str(exc)[:200]}


# ── Agent prompt + loop ──────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Domain Quality Analyst for Brevo's outbound TAM.

For each row, decide the domain's status and the company's role, then save a verdict.

WORKFLOW (default ordering — adapt as needed):
1. Call detect_bogus_pattern(domain) — cheap regex check.
2. Call find_companies_sharing_domain(domain, exclude_id=<current row id>) to see siblings.
3. REASON about the result:
   • detect_bogus said TRUE → domain is bogus. Try web_search for "<company name> official website <country>". If you find a real primary domain, save verdict status='corrected' with domain_corrected_to=<new domain>. If nothing credible found, status='bogus'.
   • Many UNRELATED siblings (different industries/brands) → bogus shared domain. Treat same as bogus.
   • Many RELATED siblings (e.g., all named "<Brand> X") → legitimate chain.
       - If THIS row is a property / branch / franchisee → status='subsidiary', domain_role='property' (or 'branch'/'franchisee'), parent_company_name=<the chain HQ>.
       - If THIS row is a Regional / Country / Global HQ (look for keywords: "Group", "Holdings", "Worldwide", "Germany", "UK Ltd", "EMEA", "International", "plc", "AG", "SA") → status='verified', domain_role='regional_hq' (or 'country_hq'/'global_hq'). KEEP.
   • Few or no siblings AND not bogus → status='verified', domain_role='independent'.
4. End by calling save_verdict.

RULES:
- Most rows resolve in 1-3 tool calls. Don't loop.
- Use web_search SPARINGLY (max 3 calls). Skip it whenever detect_bogus + find_companies gives you enough signal.
- When in doubt between property/branch/franchisee, default to 'property' for hotels/wellness, 'branch' for retail, 'franchisee' for QSR.
- ALWAYS end with save_verdict — otherwise the row stays un-checked.
"""


async def _process_one_row(client: anthropic.AsyncAnthropic, row: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        messages = [{
            "role": "user",
            "content": (
                f"Process this row:\n"
                f"  row_id:       {row['id']}\n"
                f"  company_name: {row.get('company_name')}\n"
                f"  market:       {row.get('market')}\n"
                f"  domain:       {row.get('domain')}"
            ),
        }]

        verdict = None
        turns = 0
        try:
            while turns < _MAX_TURNS:
                turns += 1
                resp = await client.messages.create(
                    model=_MODEL,
                    max_tokens=_MAX_TOKENS,
                    system=_SYSTEM_PROMPT,
                    tools=_TOOL_SCHEMAS,
                    messages=messages,
                )

                if resp.stop_reason == "end_turn":
                    break

                # web_search is a server-side tool — Anthropic executes inline.
                # We only need to respond to CUSTOM tool_use blocks.
                custom_tool_uses = [
                    b for b in resp.content
                    if getattr(b, "type", None) == "tool_use" and b.name in _CUSTOM_TOOLS
                ]

                if not custom_tool_uses:
                    # Either web_search-only turn or model finished without tools — exit
                    break

                messages.append({"role": "assistant", "content": resp.content})

                tool_results = []
                for tu in custom_tool_uses:
                    result = _execute_custom_tool(tu.name, tu.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps(result),
                    })
                    if tu.name == "save_verdict" and result.get("ok"):
                        verdict = tu.input

                messages.append({"role": "user", "content": tool_results})

                if verdict:
                    break
        except Exception as exc:
            logger.exception("agent: row %s (%s) failed", row.get("id"), row.get("domain"))
            return {"row_id": row["id"], "status": "error", "error": str(exc)[:200], "turns": turns}

        if not verdict:
            # Fallback so the row doesn't re-run forever on the cron
            _skill_save_verdict(row["id"], domain_status="unverified")
            logger.warning("agent: row %s (%s) — no verdict after %d turns, marked unverified",
                           row["id"], row.get("domain"), turns)

        return {
            "row_id":  row["id"],
            "domain":  row.get("domain"),
            "status":  "ok" if verdict else "unverified",
            "verdict": verdict,
            "turns":   turns,
        }


# ── Orchestrator ─────────────────────────────────────────────────────────────

async def run_domain_quality_check(limit: int | None = None, parked_only: bool = False) -> dict:
    """Process all qualified_tam_v2 rows where domain_quality_checked_at IS NULL.

    parked_only=True restricts processing to the rows whose
    (domain, market, company_name) tuple appears in priority_tam_parked
    (i.e. the 1,956 rows we moved aside on 2026-06-24 because they shared a
    domain with another row). Useful for the one-off triage backfill.
    """
    rows = fetch_all(
        "qualified_tam_v2",
        "id, domain, market, company_name",
        [("is_", "domain_quality_checked_at", "null")],
        limit=(None if parked_only else limit),
    )

    if parked_only:
        parked = fetch_all("priority_tam_parked", "domain, market, company_name")
        parked_keys = {(p["domain"], p["market"], p["company_name"]) for p in parked}
        rows = [r for r in rows
                if (r["domain"], r["market"], r["company_name"]) in parked_keys]
        if limit:
            rows = rows[:limit]
        logger.info("domain_quality: parked_only filter → %d rows", len(rows))

    logger.info("domain_quality: %d rows to process (limit=%s, parked_only=%s)",
                len(rows), limit, parked_only)
    if not rows:
        return {"status": "ok", "processed": 0, "message": "no rows pending"}

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sem = asyncio.Semaphore(_MAX_INFLIGHT)

    results = await asyncio.gather(*[_process_one_row(client, r, sem) for r in rows])

    by_status, by_verdict_status, by_verdict_role = {}, {}, {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        v = (r.get("verdict") or {})
        if v.get("domain_status"):
            by_verdict_status[v["domain_status"]] = by_verdict_status.get(v["domain_status"], 0) + 1
        if v.get("domain_role"):
            by_verdict_role[v["domain_role"]] = by_verdict_role.get(v["domain_role"], 0) + 1

    logger.info("domain_quality: done — status=%s verdicts=%s roles=%s",
                by_status, by_verdict_status, by_verdict_role)
    return {
        "status":            "ok",
        "processed":         len(rows),
        "by_status":         by_status,
        "by_verdict_status": by_verdict_status,
        "by_verdict_role":   by_verdict_role,
    }


# ── FastAPI router ───────────────────────────────────────────────────────────

@router.post("/pipelines/domain-quality")
async def domain_quality_endpoint(background_tasks: BackgroundTasks, limit: int | None = None):
    async def _run():
        await run_domain_quality_check(limit=limit)
    background_tasks.add_task(_run)
    return {"status": "accepted", "background": True, "limit": limit}
