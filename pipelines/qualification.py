import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException

from db.client import get_supabase, fetch_all

logger = logging.getLogger(__name__)
router = APIRouter()

TECHSTACK_API_BASE_URL = os.environ.get("TECHSTACK_API_BASE_URL", "https://techstack-api-pzd1.onrender.com")
BREVO_CRM_BASE_URL = "https://api.brevo.com/v3"

# Hard cap documented by the Technographics API: 30 requests/minute, no per-key
# burst allowance. _TECH_CONCURRENCY > 1 exists to overlap request latency
# (~10s warm, 30-60s cold-start on Render's free tier) against that ceiling —
# without it, serial calls are latency-bound (~6/min at 10s/call), well under
# what the rate limit would actually allow.
_TECH_RATE_LIMIT   = 30
_TECH_RATE_WINDOW  = 60.0
_TECH_CONCURRENCY  = 1  # temporarily serialized to test whether concurrency=6
                        # piling up requests against a cold-starting backend is
                        # causing the persistent 429s seen 2026-07-16 — revert
                        # to 6 once confirmed either way.

# The API's category lists (esp, crm, etc.) mix in email-auth DNS artifacts
# (SPF/DKIM/DMARC/BIMI records) that aren't real tools — filtered out before scoring.
_NOISE_SUBSTRINGS = ("spf", "dkim", "dmarc", "bimi")

_TECH_LIST_CATEGORIES = [
    "crm", "cms", "ecommerce", "analytics", "cdn",
    "payment", "marketing", "chat", "hosting", "ab_testing", "tag_manager",
]

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

async def run_crm_check(limit: int = 1000) -> dict:
    """
    Fetches up to `limit` unchecked rows per market from sourced_tam_v2,
    calls Brevo CRM API per domain, writes CRM fields back, and marks
    crm_checked=true. Default limit=1000 for daily runs; pass higher to clear backlog.
    """
    sb = get_supabase()
    rows = fetch_all(
        "sourced_tam_v2", "domain, market",
        [("eq", "crm_checked", False)],
        limit=limit,
    )

    if not rows:
        logger.info("crm_check: no unchecked rows remaining")
        return {"status": "ok", "processed": 0}

    logger.info("crm_check: processing %d domains", len(rows))
    semaphore = asyncio.Semaphore(25)

    async def fetch_one(row: dict) -> None:
        domain = row["domain"]
        async with semaphore:
            try:
                async with httpx.AsyncClient(http2=False) as client:
                    crm = await get_brevo_company(domain, client)
                update_payload = crm if crm else {
                    "brevo_company_id": None,
                    "open_deals":       None,
                    "deal_lost_date":   None,
                    "planhat_id":       None,
                }
                update_payload["crm_checked"] = True
                sb.table("sourced_tam_v2").update(update_payload).eq("domain", domain).eq("market", row["market"]).execute()
            except Exception as exc:
                logger.error("crm_check: failed for %s: %s", domain, exc)

    await asyncio.gather(*[fetch_one(r) for r in rows])
    logger.info("crm_check: wrote crm fields for %d domains", len(rows))
    by_market = {}
    for r in rows:
        by_market[r["market"]] = by_market.get(r["market"], 0) + 1
    return {"status": "ok", "processed": len(rows), "by_market": by_market}


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
        "location, country, linkedin_url, vertical, tam_segment, "
        "brevo_company_id, planhat_id, open_deals, deal_lost_date",
        [("eq", "crm_checked", True), ("eq", "qualification_checked", False)],
    )

    if not rows:
        logger.info("qualification_rules: no unprocessed rows")
        return {"status": "ok", "qualified": 0, "newly_qualified": 0, "disqualified": 0}

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
                "tam_segment":       row.get("tam_segment"),
                "brevo_company_id":  row.get("brevo_company_id"),
                "planhat_id":        row.get("planhat_id"),
                "open_deals":        row.get("open_deals"),
                "deal_lost_date":    row.get("deal_lost_date"),
            })
        else:
            disqualified += 1

    # keep only the highest sourced_tam_id row per (domain, market, company_name)
    best: dict[tuple, dict] = {}
    for r in qualified_rows:
        key = (r["domain"], r["market"], r.get("company_name"))
        if key not in best or r["sourced_tam_id"] > best[key]["sourced_tam_id"]:
            best[key] = r
    deduped = list(best.values())

    before = sb.table("qualified_tam_v2").select("id", count="exact").execute().count or 0

    if deduped:
        for i in range(0, len(deduped), 100):
            chunk = deduped[i : i + 100]
            sb.rpc("upsert_qualified_tam_v2", {"p_rows": chunk}).execute()

    after = sb.table("qualified_tam_v2").select("id", count="exact").execute().count or 0

    # Mark all processed rows so they are not re-evaluated on future runs
    processed_ids = [row["id"] for row in rows]
    for i in range(0, len(processed_ids), 100):
        sb.table("sourced_tam_v2").update({"qualification_checked": True}).in_("id", processed_ids[i : i + 100]).execute()

    logger.info("qualification_rules: qualified=%d deduped=%d disqualified=%d newly_added=%d", len(qualified_rows), len(deduped), disqualified, after - before)
    return {"status": "ok", "qualified": len(deduped), "newly_qualified": after - before, "disqualified": disqualified}


# ── Technographic API call ────────────────────────────────────────────────────

class _AsyncRateLimiter:
    """Strict evenly-paced limiter: enforces a minimum interval between
    consecutive dispatches (60/limit seconds apart), not a sliding-window count.

    A sliding window allows bursts — e.g. concurrency letting several requests
    all dispatch within the same instant once the window has "room" — and a
    live production run confirmed this Technographic API rejects those bursts
    with 429s even while the 60s average stays under the documented 30/min cap.
    It behaves like a strict token bucket, not a smooth window, so we now match
    that: the lock is held for the ENTIRE sleep, serializing every dispatch to
    one every ~2s regardless of how many coroutines are waiting."""

    def __init__(self, limit: int = _TECH_RATE_LIMIT, window: float = _TECH_RATE_WINDOW):
        self._min_interval = window / limit
        self._lock = asyncio.Lock()
        self._last_dispatch = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait_for = self._min_interval - (now - self._last_dispatch)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_dispatch = asyncio.get_event_loop().time()


def _clean_tool_names(tools: list[dict] | None) -> list[str]:
    """Strips SPF/DKIM/DMARC/BIMI auth-artifact noise, prefers high-confidence
    names, falls back to medium if no high-confidence names remain."""
    if not tools:
        return []
    filtered = [
        t for t in tools
        if t.get("name") and not any(n in t["name"].lower() for n in _NOISE_SUBSTRINGS)
    ]
    high = [t["name"] for t in filtered if t.get("confidence") == "high"]
    if high:
        return high
    return [t["name"] for t in filtered if t.get("confidence") == "medium"]


def _flatten_tools(tools: list[dict] | None) -> str | None:
    names = _clean_tool_names(tools)
    return "|".join(names) if names else None


async def get_techstack(domain: str, client: httpx.AsyncClient) -> dict:
    """Calls the Technographics API. Caller is responsible for rate-limiting
    (30 req/min hard cap) and for handling 429/404/other errors."""
    resp = await client.get(
        f"{TECHSTACK_API_BASE_URL}/api/techstack",
        params={"domain": domain, "mode": "smart"},
        headers={"X-API-Key": os.environ["TECHSTACK_API_KEY"]},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


# ── Step 4: Technographic enrichment ─────────────────────────────────────────

async def run_technographic() -> dict:
    """
    Reads qualified_tam_v2 rows not yet checked (tech_checked_at IS NULL), calls
    the Technographics API respecting the hard 30 req/min limit, and writes the
    tech_* columns + derived esp_detected/esp_score back.

    429 -> sleep 60s, retry once, then give up on this row for this run (retried
           next run since tech_checked_at is left untouched).
    404 -> domain not found; mark checked with all tech_* fields left null.
    other 4xx/5xx or network error -> log + leave for retry next run.

    Guarded by a Supabase-backed lock (pipeline_locks) so a concurrent call —
    e.g. the daily-pipeline cron firing mid-way through a large manual backlog
    run — skips instead of spinning up a second _AsyncRateLimiter that would
    compete for the same external 30 req/min budget and risk 429 storms.
    """
    sb = get_supabase()
    try:
        sb.table("pipeline_locks").insert({"name": "technographic"}).execute()
    except Exception:
        logger.warning("technographic: lock already held — skipping this run (another call is in progress)")
        return {"status": "skipped", "reason": "already_running", "processed": 0}

    try:
        return await _run_technographic_locked(sb)
    finally:
        sb.table("pipeline_locks").delete().eq("name", "technographic").execute()


async def _run_technographic_locked(sb) -> dict:
    rows = fetch_all("qualified_tam_v2", "domain, market", [("is_", "tech_checked_at", "null")])

    if not rows:
        logger.info("technographic: no rows to process")
        return {"status": "ok", "processed": 0}

    logger.info("technographic: processing %d domains", len(rows))
    limiter = _AsyncRateLimiter()
    semaphore = asyncio.Semaphore(_TECH_CONCURRENCY)

    async def fetch_one(row: dict) -> dict | None:
        domain, market = row["domain"], row["market"]
        async with semaphore:
            await limiter.wait()
            async with httpx.AsyncClient() as client:
                try:
                    data = await get_techstack(domain, client)
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if status == 429:
                        await asyncio.sleep(60)
                        try:
                            data = await get_techstack(domain, client)
                        except Exception:
                            logger.error("techstack: 429 retry failed for %s", domain)
                            return None
                    elif status == 404:
                        return {"domain": domain, "market": market, "payload": {}}
                    else:
                        logger.error("techstack: HTTP %s for %s", status, domain)
                        return None
                except Exception as exc:
                    logger.error("techstack: request failed for %s: %s", domain, exc)
                    return None

            esp_names = _clean_tool_names(data.get("esp"))
            esp_list = [{"name": n} for n in esp_names]
            payload = {
                "tech_score":          data.get("tech_score"),
                # Doc says "tech_score_primary"; live API actually returns "tech_stack_primary" —
                # check both (France_TAM's own client independently hit the same discrepancy).
                "tech_stack_primary":  data.get("tech_stack_primary") or data.get("tech_score_primary"),
                "tech_category":       data.get("tech_category"),
                "tech_esp":            "|".join(esp_names) if esp_names else None,
                "esp_detected":        get_primary_esp(esp_list) if esp_list else None,
                "esp_score":           compute_esp_score(esp_list),
            }
            for category in _TECH_LIST_CATEGORIES:
                payload[f"tech_{category}"] = _flatten_tools(data.get(category))
            return {"domain": domain, "market": market, "payload": payload}

    results = await asyncio.gather(*[fetch_one(r) for r in rows])
    enriched = [r for r in results if r is not None]

    # Each write is isolated: a transient failure on one row must not throw away
    # every already-fetched result queued after it in this list. (A live run lost
    # ~12k successfully-checked domains this way — the loop hit one bad write,
    # raised, and skipped straight past the final "wrote" log with nothing
    # persisted for anything still unwritten at that point.)
    now_iso = datetime.now(timezone.utc).isoformat()
    write_failures = 0
    for r in enriched:
        payload = {**r["payload"], "tech_checked_at": now_iso}
        try:
            sb.table("qualified_tam_v2").update(payload).eq("domain", r["domain"]).eq("market", r["market"]).execute()
        except Exception as exc:
            write_failures += 1
            logger.error("technographic: write failed for %s/%s: %s — left for retry", r["domain"], r["market"], exc)

    left_for_retry = len(rows) - len(enriched) + write_failures
    logger.info("technographic: wrote %d results (%d write failures, %d left for retry)",
                len(enriched) - write_failures, write_failures, left_for_retry)
    return {"status": "ok", "processed": len(enriched) - write_failures, "left_for_retry": left_for_retry}


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/pipelines/qualify")
async def run_qualification(background_tasks: BackgroundTasks, crm_limit: int = 1000):
    """Runs Steps 2-4 in background: CRM check → qualification rules → technographic.

    crm_limit caps how many crm_checked=False rows Step 2 processes in this call
    (default 1000 for the normal daily cron). Pass a higher value to clear a large
    backlog in one shot — e.g. after a bulk sourced_tam_v2 import."""
    async def _run():
        from utils.slack import notify
        try:
            crm = await run_crm_check(limit=crm_limit)
            rules = await run_qualification_rules()
            tech = await run_technographic()
            await notify(
                f"✅ *Qualify pipeline complete*\n"
                f"• CRM checked: +{crm['processed']:,}\n"
                f"• Newly qualified: +{rules['newly_qualified']:,} | disqualified: {rules['disqualified']:,}\n"
                f"• Technographic: {tech['processed']:,} processed"
            )
        except Exception as exc:
            from utils.slack import notify
            await notify(f"❌ *Qualify pipeline failed* — `{exc}`", success=False)
            logger.exception("qualify: failed")
    background_tasks.add_task(_run)
    return {"status": "started"}


@router.post("/pipelines/crm-check")
async def crm_check_endpoint(background_tasks: BackgroundTasks, limit: int = 1000):
    """Run CRM check in background. Use limit=10000 to clear backlog."""
    async def _run():
        from utils.slack import notify
        try:
            result = await run_crm_check(limit=limit)
            await notify(
                f"✅ *CRM check complete*\n"
                f"• Processed: {result['processed']:,} companies\n"
                + "\n".join(f"  ↳ {m}: {c:,}" for m, c in result.get("by_market", {}).items())
            )
        except Exception as exc:
            from utils.slack import notify
            await notify(f"❌ *CRM check failed* — `{exc}`", success=False)
            logger.exception("crm_check_endpoint: failed")
    background_tasks.add_task(_run)
    return {"status": "started", "limit": limit}
