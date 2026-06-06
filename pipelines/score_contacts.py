"""Claude-driven scoring of PhantomBuster-sourced contacts.

Two stages, deliberately split so the user can review qualified candidates before
they hit sourced_contacts:

  1. score_contacts()   — score every unscored phantombuster_contacts row on TWO
                          dimensions (relevance + seniority).  No promotion.
  2. preview_top_n()    — read-only: top N per domain where relevance >= 3,
                          ordered by (relevance DESC, seniority DESC).
  3. promote_top_n()    — write the same top-N selection to sourced_contacts.

The split exists because high-volume retailers (Marks & Spencer returned 360 PB
contacts) need a relevance+seniority ranking — picking any-10-with-score>=3 was
leaving Head of CRM (5/5) behind Lifecycle CRM Manager (5/3) in some domains.
"""
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all
from utils.slack import notify

logger = logging.getLogger(__name__)
router = APIRouter()

PROMPT_TEMPLATE = """You are a sales targeting analyst for Brevo, a CRM and marketing
automation platform for B2B and B2C companies.

Your job is to score how relevant a contact is as an outbound
target for Brevo based solely on their job title, on TWO independent
dimensions: relevance and seniority.

Brevo's ideal contacts are people who own, influence, or make
decisions about email marketing, CRM, customer communications,
marketing automation, or loyalty programmes.

Contact details:
- Job title: {title}
- Company name: {company}

===============================================================
RELEVANCE_SCORE (1-5) — how well their function fits Brevo's ICP
===============================================================

5 — Direct owner
Directly owns and operates email, CRM, marketing automation,
or loyalty platforms day-to-day.
Examples: CRM Manager, Email Marketing Manager, Head of CRM,
Marketing Automation Manager, Loyalty Manager, Head of Retention,
Lifecycle Marketing Manager, Customer Engagement Manager

4 — Strong influencer
Leads the broader marketing function and directly influences
or approves CRM/email tooling decisions.
Examples: Marketing Director, Head of Marketing, VP Marketing,
Head of Digital Marketing, CMO

3 — Adjacent influencer
Works within marketing but focus is on a related area that
occasionally intersects with email/CRM decisions.
Examples: Head of Growth, Growth Manager, Head of E-commerce,
Digital Marketing Manager, Marketing Operations Manager

2 — Weak signal
Sits within the marketing umbrella but primary focus is on
channels unrelated to email, CRM, or owned communications.
Examples: Paid Marketing Manager, SEO Manager, Social Media Manager,
Performance Marketing Manager, Brand Manager

1 — Not relevant
No connection to marketing, CRM, or customer communications.
Examples: Sales Manager, HR Director, Finance Manager, Engineer,
Operations Manager, Customer Support, Office Manager

Rules for relevance_score:
- Score based on the job title alone — company fit is already confirmed
- If ambiguous, score the most likely interpretation of the role
- If the title is generic (e.g. "Manager", "Director") with no
  department context, score 1
- Paid, performance, and acquisition-focused titles score maximum 2
  regardless of seniority

===============================================================
SENIORITY_SCORE (1-5) — how senior the person is, independent of function
===============================================================

5 — C-suite / Head of
CEO, COO, CMO, CRO, Chief X Officer, Founder, Owner, Head of <function>

4 — Director / VP
Director, Senior Director, VP, SVP, EVP

3 — Senior Manager / Lead
Senior Manager, Lead, Principal, Team Lead, Group Manager

2 — Manager
Manager, Specialist, Senior Specialist (without Lead/Principal)

1 — Executive / IC / Coordinator / Assistant
Executive, Assistant, Coordinator, Associate, Analyst, Intern,
Apprentice, or any title with no clear leadership indicator

Rules for seniority_score:
- Score the seniority signal in the title alone
- "Head of X" → 5 even if X is a niche area
- "Senior X" where X is an IC title (e.g. Senior Marketing Executive)
  → 1, not 3. "Senior" alone is not a leadership signal.
- "Lead X" or "X Lead" → 3
- If the title gives no seniority signal at all, score 2

===============================================================

Return your answer in this exact JSON format with no preamble, no
markdown code fences, and no text outside it:

{{
  "relevance_score": 0,
  "seniority_score": 0,
  "reasoning": ""
}}"""

MODEL = "claude-haiku-4-5-20251001"
RELEVANCE_THRESHOLD = 3   # relevance_score >= this is eligible for promotion
DEFAULT_TOP_N       = 10  # cap per domain


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(text: str) -> dict:
    """Pull the JSON object from a Claude response, stripping any code fences or prose."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# ── Stage 1: scoring ───────────────────────────────────────────────────────────

def score_contacts(batch_number: int | None = None) -> dict:
    """Submit unscored phantombuster_contacts to Claude Batch API, persist
    relevance + seniority scores. No promotion."""
    filters: list = [("is_", "scored_at", "null")]
    if batch_number is not None:
        filters.append(("eq", "batch_number", batch_number))

    rows = fetch_all(
        "phantombuster_contacts",
        "id,domain,company_name,batch_number,job_title",
        filters=filters,
    )
    if not rows:
        logger.info("score_contacts: nothing to score")
        return {"status": "ok", "scored": 0}

    client = _client()
    reqs = []
    for r in rows:
        prompt = PROMPT_TEMPLATE.format(
            title=r.get("job_title") or "",
            company=r.get("company_name") or "",
        )
        reqs.append({
            "custom_id": f"pbc_{r['id']}",
            "params": {
                "model": MODEL,
                "max_tokens": 250,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    logger.info("score_contacts: submitting batch of %d", len(reqs))
    batch = client.messages.batches.create(requests=reqs)
    logger.info("score_contacts: batch id %s", batch.id)

    while True:
        b = client.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        time.sleep(10)

    sb = get_supabase()
    scored = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for line in client.messages.batches.results(batch.id):
        if line.result.type != "succeeded":
            logger.warning("score_contacts: %s failed: %s", line.custom_id, line.result)
            continue
        contact_id = line.custom_id.replace("pbc_", "")
        parsed = _extract_json(line.result.message.content[0].text)
        relevance = parsed.get("relevance_score")
        seniority = parsed.get("seniority_score")
        reasoning = parsed.get("reasoning")
        if not isinstance(relevance, int) or not isinstance(seniority, int):
            logger.warning("score_contacts: invalid scores for %s: %s", contact_id, parsed)
            continue
        sb.table("phantombuster_contacts").update({
            "relevance_score":     relevance,
            "seniority_score":     seniority,
            "relevance_reasoning": reasoning,
            "scored_at":           now_iso,
        }).eq("id", contact_id).execute()
        scored += 1

    logger.info("score_contacts: scored=%d", scored)
    return {"status": "ok", "scored": scored, "batch_id": batch.id}


# ── Stage 2: preview top-N per domain ──────────────────────────────────────────

def preview_top_n_per_domain(
    batch_number: int | None = None,
    n: int = DEFAULT_TOP_N,
    threshold: int = RELEVANCE_THRESHOLD,
) -> dict:
    """Read-only: return the candidate list that would be promoted, grouped by
    domain, ordered by (relevance DESC, seniority DESC, job_title)."""
    filters: list = [
        ("eq", "promoted_to_sourced_contacts", False),
        ("gte", "relevance_score", threshold),
    ]
    if batch_number is not None:
        filters.append(("eq", "batch_number", batch_number))

    rows = fetch_all(
        "phantombuster_contacts",
        "id,domain,company_name,first_name,last_name,job_title,linkedin_url,"
        "relevance_score,seniority_score,relevance_reasoning",
        filters=filters,
    )

    by_domain: dict[str, list[dict]] = {}
    for r in rows:
        by_domain.setdefault(r["domain"], []).append(r)

    qualified: dict[str, list[dict]] = {}
    for domain, items in by_domain.items():
        items.sort(
            key=lambda x: (
                -(x.get("relevance_score") or 0),
                -(x.get("seniority_score") or 0),
                (x.get("job_title") or "").lower(),
            )
        )
        qualified[domain] = items[:n]

    total = sum(len(v) for v in qualified.values())
    return {
        "status":     "ok",
        "domains":    len(qualified),
        "candidates": total,
        "qualified":  qualified,
    }


# ── Stage 3: promote top-N per domain ─────────────────────────────────────────

def promote_top_n_per_domain(
    batch_number: int | None = None,
    n: int = DEFAULT_TOP_N,
    threshold: int = RELEVANCE_THRESHOLD,
) -> dict:
    """Write the top-N qualified contacts per domain to sourced_contacts.

    Clay precedence: if a (domain, email) row already exists with source='clay',
    we skip the upsert (PB never overwrites Clay-sourced contacts). The PB row
    is still marked promoted_to_sourced_contacts=true so it falls out of future
    runs."""
    preview = preview_top_n_per_domain(batch_number, n, threshold)
    qualified = preview["qualified"]
    if not qualified:
        return {"status": "ok", "promoted": 0, "domains": 0}

    sb = get_supabase()
    promoted_count = 0
    pbc_ids_to_mark: list[str] = []

    for domain, items in qualified.items():
        # Get the full row (incl. raw/email/market/batch_number) for each candidate
        ids = [i["id"] for i in items]
        full = fetch_all(
            "phantombuster_contacts",
            "id,domain,company_name,market,batch_number,first_name,last_name,"
            "job_title,linkedin_url,email,raw,relevance_score,seniority_score,"
            "relevance_reasoning",
            filters=[("in_", "id", ids)],
        )
        for r in full:
            skip_upsert = False
            if r.get("email"):
                existing = sb.table("sourced_contacts").select("id,source").eq(
                    "domain", r["domain"]
                ).eq("email", r["email"]).limit(1).execute().data
                if existing and existing[0].get("source") == "clay":
                    skip_upsert = True

            if not skip_upsert:
                sourced_row = {
                    "domain":              r["domain"],
                    "company_name":        r["company_name"],
                    "market":              r["market"],
                    "batch_number":        r["batch_number"],
                    "source":              "linkedin",
                    "email":               r.get("email"),
                    "first_name":          r.get("first_name"),
                    "last_name":           r.get("last_name"),
                    "job_title":           r.get("job_title"),
                    "linkedin_url":        r.get("linkedin_url"),
                    "relevance_score":     r.get("relevance_score"),
                    "seniority_score":     r.get("seniority_score"),
                    "relevance_reasoning": r.get("relevance_reasoning"),
                    "raw":                 r.get("raw"),
                }
                if r.get("email"):
                    sb.table("sourced_contacts").upsert(
                        sourced_row, on_conflict="domain,email"
                    ).execute()
                else:
                    sb.table("sourced_contacts").insert(sourced_row).execute()
                promoted_count += 1

            pbc_ids_to_mark.append(r["id"])

    if pbc_ids_to_mark:
        sb.table("phantombuster_contacts").update({
            "promoted_to_sourced_contacts": True,
        }).in_("id", pbc_ids_to_mark).execute()

    return {
        "status":   "ok",
        "domains":  len(qualified),
        "promoted": promoted_count,
    }


# ── FastAPI ───────────────────────────────────────────────────────────────────

async def _run_score_bg(batch_number: int | None) -> None:
    try:
        result = score_contacts(batch_number)
        if result["scored"] > 0:
            await notify(
                f"🧠 *Contact scoring complete*\n"
                f"• Scored: {result['scored']}\n"
                f"• Next step: GET /pipelines/score-contacts/preview to review "
                f"top-{DEFAULT_TOP_N}-per-domain before promotion"
            )
        else:
            logger.info("score_contacts: no rows to score, skipping Slack notification")
    except Exception as exc:
        await notify(f"❌ *Contact scoring failed* — `{exc}`", success=False)
        logger.exception("score_contacts: failed")


@router.post("/pipelines/score-contacts")
async def score_contacts_endpoint(background_tasks: BackgroundTasks, batch_number: int | None = None):
    """Daily cron: score all unscored phantombuster_contacts on relevance + seniority.
    Does NOT promote — call /pipelines/score-contacts/promote after review."""
    background_tasks.add_task(_run_score_bg, batch_number)
    return {"status": "started", "batch_number": batch_number}


@router.get("/pipelines/score-contacts/preview")
def score_contacts_preview(
    batch_number: int | None = None,
    n: int = DEFAULT_TOP_N,
    threshold: int = RELEVANCE_THRESHOLD,
):
    """Read-only preview of the top-N qualified contacts per domain that would
    be promoted to sourced_contacts. Returns the full ranked list grouped by
    domain so you can spot-check before calling /promote."""
    return preview_top_n_per_domain(batch_number, n, threshold)


@router.post("/pipelines/score-contacts/promote")
async def score_contacts_promote(
    batch_number: int | None = None,
    n: int = DEFAULT_TOP_N,
    threshold: int = RELEVANCE_THRESHOLD,
):
    """Promote the top-N qualified contacts per domain to sourced_contacts.
    Synchronous (no background task) so the caller sees the count immediately."""
    result = promote_top_n_per_domain(batch_number, n, threshold)
    await notify(
        f"✅ *Contact promotion complete*\n"
        f"• Domains: {result['domains']}\n"
        f"• Promoted to sourced_contacts: {result['promoted']}"
    )
    return result
