"""Classify Lemlist replies into actionable buckets via Claude.

Reads emailsReplied events from lemlist_activities, strips quoted history
from the reply text, sends the cleaned text + subject + sender info to
Claude, parses the structured JSON response, and writes a row to
reply_classifications (idempotent on lemlist_activities.id via the
lemlist_activity_id unique index from migration 042).

Classification taxonomy (10 buckets):
  positive_meeting_request   → schedule_meeting
  positive_interested        → escalate_bdr
  neutral_question           → escalate_bdr
  neutral_referral           → reroute_to_referral
  negative_not_now           → add_to_nurture
  negative_unsubscribe       → unsubscribe + blacklist
  negative_complaint         → unsubscribe + blacklist
  oof                        → wait_for_return (extracts requeue_date)
  conversation_in_progress   → mark_in_conversation
  unclear                    → none
"""
import asyncio
import json
import logging
import os
import re
from datetime import date, datetime

import anthropic

from db.client import get_supabase, fetch_all

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"
_MAX_INFLIGHT = 15

# Scope: only classify replies from the UKI ABM v2 campaign — lemlist_activities
# ingests events for every Brevo Lemlist sender across the company, but we only
# care about our own outbound. Will graduate to the abm_campaigns reference
# table once that's built.
_ABM_CAMPAIGN_ID = "cam_cjkdYRBDEZFaXXYxo"

# Markers signalling start of quoted history — text BEFORE the first match
# is the new reply we care about. Patterns are matched line-leading and
# case-insensitively where appropriate.
_QUOTE_MARKERS = [
    # Gmail-style: "On Wed, Jun 17, 2026 at 3:39 PM Joe <joe@x.com> wrote:"
    re.compile(r"^\s*On\s+.{1,200}\s+wrote:\s*$", re.IGNORECASE | re.MULTILINE),
    # Outlook header blocks
    re.compile(r"^\s*From:\s+.+$", re.MULTILINE),
    re.compile(r"^\s*Sent:\s+.+$", re.MULTILINE),
    # Outlook reply separator (long underscore line)
    re.compile(r"^_{10,}\s*$", re.MULTILINE),
    # Original message header
    re.compile(r"^\s*-{3,}\s*Original Message\s*-{3,}\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*-{3,}\s*Forwarded message\s*-{3,}\s*$", re.IGNORECASE | re.MULTILINE),
    # Standard sig delimiter
    re.compile(r"^--\s*$", re.MULTILINE),
]

# Lines starting with > are quoted content; if a block of these appears,
# strip from the first one onwards
_QUOTED_LINE_RE = re.compile(r"^>", re.MULTILINE)


def extract_new_reply(text: str) -> str:
    """Strip quoted history + signatures from a reply, returning just the
    new content the prospect actually wrote. Falls back to the full text
    if no markers are found (some short replies have no quoted history)."""
    if not text:
        return ""

    # Find earliest position of any quote marker
    earliest = len(text)
    for pat in _QUOTE_MARKERS:
        m = pat.search(text)
        if m and m.start() < earliest:
            earliest = m.start()

    # Also check quoted-line blocks
    m = _QUOTED_LINE_RE.search(text)
    if m and m.start() < earliest:
        earliest = m.start()

    trimmed = text[:earliest].strip()

    # If we trimmed too aggressively (left nothing useful), return the
    # first 2000 chars of the original — better some context than none
    if len(trimmed) < 20:
        return text[:2000].strip()

    # Cap at 4000 chars even if no markers were found, to keep Claude
    # tokens predictable
    return trimmed[:4000]


_SYSTEM_PROMPT = (
    "You classify replies to outbound sales emails sent by Brevo's BDR team. "
    "You always return ONLY a single JSON object — no preamble, no markdown fences."
)


_USER_PROMPT_TEMPLATE = """Classify this reply from {sender_email} to a Brevo outbound email.

ORIGINAL EMAIL SUBJECT:
{subject}

REPLY (quoted history already stripped):
{reply_text}

---

Classify into ONE of these categories:

| category | when |
|---|---|
| positive_meeting_request | Wants a meeting / demo / calendar invite explicitly |
| positive_interested | Wants more info, asks for pricing, says "interested" without committing to a meeting |
| neutral_question | Asks a specific feature/pricing question without commitment |
| neutral_referral | Says "talk to X instead" — names another person at the company |
| negative_not_now | Polite "not a priority right now" / "circle back later" |
| negative_unsubscribe | Asks to be removed, stop emailing, unsubscribe |
| negative_complaint | Angry, calls it spam, threatens legal action |
| oof | Out-of-office auto-responder (mentions return date or "currently away") |
| conversation_in_progress | Mid-thread BDR conversation already in progress (discussing contracts, follow-ups to a meeting, etc.) — not a fresh first-touch reply |
| unclear | Can't determine the category from the reply text |

Also extract any of these if present, else null:
- referral_email: email of a person the prospect redirects you to
- referral_name: name of that person
- mentioned_competitor: name of a competing tool the prospect mentions (Mailchimp, Klaviyo, HubSpot, Marketo, Pardot, ActiveCampaign, Iterable, Braze, MoEngage, Customer.io, Sailthru, etc.)
- requeue_date: ISO date (YYYY-MM-DD) if reply is OOF and mentions a return date, OR if reply says "ask me again in [time]"

Return ONLY this JSON, no preamble, no markdown:
{{
  "classification": "<one of the categories above>",
  "confidence": <float between 0 and 1>,
  "reasoning": "<one short sentence explaining the classification>",
  "recommended_action": "<one of: schedule_meeting | escalate_bdr | reroute_to_referral | add_to_nurture | unsubscribe | mark_in_conversation | wait_for_return | none>",
  "requeue_date": "<YYYY-MM-DD or null>",
  "referral_email": "<email or null>",
  "referral_name": "<name or null>",
  "mentioned_competitor": "<tool name or null>"
}}"""


def _build_prompt(reply_text: str, subject: str, sender_email: str) -> str:
    return _USER_PROMPT_TEMPLATE.format(
        subject=subject or "(no subject)",
        sender_email=sender_email or "(unknown)",
        reply_text=reply_text or "(empty)",
    )


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    t = text.strip()
    if "```" in t:
        t = t.split("```", 1)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.rsplit("```", 1)[0]
    start, end = t.find("{"), t.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(t[start:end])
    except json.JSONDecodeError as exc:
        logger.warning("reply_intel: JSON parse failed: %s", exc)
        return None


def _coerce_date(val) -> date | None:
    """Accept 'YYYY-MM-DD' string or None; return date or None."""
    if not val or val == "null":
        return None
    try:
        return datetime.fromisoformat(str(val)).date()
    except (ValueError, TypeError):
        return None


async def classify_reply(reply_text: str, subject: str, sender_email: str) -> dict | None:
    """Single Claude call. Returns the parsed dict, or None on failure."""
    client = _get_client()
    prompt = _build_prompt(reply_text, subject, sender_email)
    try:
        msg = await client.messages.create(
            model=_MODEL,
            max_tokens=600,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        logger.exception("reply_intel: Claude call failed")
        return None

    text = msg.content[0].text if msg.content else ""
    parsed = _extract_json(text)
    if not parsed:
        return None

    return {
        "classification":       parsed.get("classification") or "unclear",
        "confidence":           float(parsed.get("confidence") or 0.0),
        "reasoning":            (parsed.get("reasoning") or "").strip()[:500],
        "action_taken":         parsed.get("recommended_action") or "none",
        "requeue_date":         _coerce_date(parsed.get("requeue_date")),
        "referral_email":       (parsed.get("referral_email") or None) or None,
        "referral_name":        (parsed.get("referral_name") or None) or None,
        "mentioned_competitor": (parsed.get("mentioned_competitor") or None) or None,
    }


def _pending_reply_rows() -> list[dict]:
    """Returns lemlist_activities rows that are emailsReplied AND not yet
    classified (idempotency check via lemlist_activity_id)."""
    sb = get_supabase()
    classified_ids = {
        r["lemlist_activity_id"]
        for r in fetch_all("reply_classifications", "lemlist_activity_id",
                           [("not.is_", "lemlist_activity_id", "null")])
        if r.get("lemlist_activity_id")
    } if False else set()
    # fetch_all's filter syntax doesn't chain not.is_; load all classified IDs directly
    res = sb.table("reply_classifications").select("lemlist_activity_id").execute().data
    classified_ids = {r["lemlist_activity_id"] for r in res if r.get("lemlist_activity_id")}

    all_replies = fetch_all(
        "lemlist_activities",
        "id, lead_email, domain, company_name, campaign_id, campaign_name, raw_payload",
        [("eq", "event_type", "emailsReplied"),
         ("eq", "campaign_id", _ABM_CAMPAIGN_ID)],
    )
    return [r for r in all_replies if r["id"] not in classified_ids]


async def classify_pending_replies(limit: int | None = None) -> dict:
    """Process all unclassified emailsReplied events. Concurrent-capped."""
    pending = _pending_reply_rows()
    if limit:
        pending = pending[:limit]

    if not pending:
        logger.info("reply_intel: nothing pending")
        return {"status": "ok", "processed": 0, "written": 0}

    logger.info("reply_intel: %d pending replies to classify", len(pending))

    sb = get_supabase()
    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    written = 0
    failed = 0

    async def _one(row: dict) -> None:
        nonlocal written, failed
        async with sem:
            payload = row.get("raw_payload") or {}
            full_text = payload.get("text") or payload.get("messagePreview") or ""
            reply_text = extract_new_reply(full_text)
            subject = payload.get("subject") or ""
            sender_email = payload.get("fromEmail") or row.get("lead_email") or ""

            result = await classify_reply(reply_text, subject, sender_email)
            if not result:
                failed += 1
                return

            try:
                sb.table("reply_classifications").insert({
                    "lemlist_activity_id":  row["id"],
                    "contact_email":        row.get("lead_email") or sender_email,
                    "domain":               row.get("domain") or payload.get("companyDomain"),
                    "company_name":         row.get("company_name") or payload.get("leadCompanyName") or payload.get("companyName"),
                    "campaign_id":          row.get("campaign_id") or payload.get("campaignId"),
                    "campaign_name":        row.get("campaign_name") or payload.get("campaignName"),
                    "reply_content":        reply_text[:8000],
                    "classification":       result["classification"],
                    "confidence":           result["confidence"],
                    "reasoning":            result["reasoning"],
                    "action_taken":         result["action_taken"],
                    "requeue_date":         result["requeue_date"].isoformat() if result["requeue_date"] else None,
                    "referral_email":       result["referral_email"],
                    "referral_name":        result["referral_name"],
                    "mentioned_competitor": result["mentioned_competitor"],
                    "raw_lemlist_payload":  payload,
                }).execute()
                written += 1
            except Exception:
                logger.exception("reply_intel: failed to persist for %s", row.get("lead_email"))
                failed += 1

    await asyncio.gather(*[_one(r) for r in pending])
    logger.info("reply_intel: done — %d written, %d failed", written, failed)
    return {
        "status":    "ok",
        "processed": len(pending),
        "written":   written,
        "failed":    failed,
    }
