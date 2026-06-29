import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

# UKI ABM v2 — the campaign we own. Auto-classification + Slack alert fires
# only for replies on this campaign (lemlist_activities ingests events from
# every Brevo Lemlist sender across the org).
_ABM_CAMPAIGN_ID = "cam_cjkdYRBDEZFaXXYxo"

# Visual cue per classification — used in the Slack notification.
_EMOJI_BY_CLASSIFICATION = {
    "positive_meeting_request": "🎯",
    "positive_interested":      "🚀",
    "neutral_question":         "❓",
    "neutral_referral":         "🔀",
    "negative_not_now":         "⏸️",
    "negative_unsubscribe":     "🚫",
    "negative_complaint":       "🚨",
    "oof":                       "🏖️",
    "conversation_in_progress": "💬",
    "unclear":                  "🤷",
}


def _validate_secret(body: dict) -> None:
    """Lemlist sends the webhook secret inside the JSON body as a 'secret' field."""
    secret = os.environ.get("LEMLIST_WEBHOOK_SECRET", "")
    if not secret:
        return
    if body.get("secret") != secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


def _parse_activity(body: dict) -> dict:
    # Lemlist stamps `bot: true|false` on emailsClicked / emailsOpened events
    # based on their bot heuristics (user-agent, IP, click timing). Other event
    # types omit the field — we store None in those cases.
    bot_val = body.get("bot")
    is_bot = bool(bot_val) if isinstance(bot_val, bool) else None

    return {
        "lead_email":    body.get("leadEmail"),
        "domain":        body.get("companyDomain"),
        "company_name":  body.get("leadCompanyName"),
        "campaign_id":   body.get("campaignId"),
        "campaign_name": body.get("campaignName") or body.get("name"),
        "lead_id":       body.get("leadId"),
        "contact_id":    body.get("contactId"),
        "event_type":    body.get("type"),
        "sequence_step": body.get("sequenceStep"),
        "created_at":    body.get("createdAt"),
        "is_bot":        is_bot,
        "raw_payload":   body,
    }


def _format_slack_message(row: dict, subject: str, reply_text: str, result: dict) -> str:
    emoji = _EMOJI_BY_CLASSIFICATION.get(result["classification"], "📨")
    lines = [
        f"{emoji} *New ABM v2 reply* — `{row.get('company_name') or row.get('domain')}`",
        f"From: `{row.get('lead_email')}`",
    ]
    if subject:
        lines.append(f"Subject: _{subject[:80]}_")
    lines.append(f"Classification: *{result['classification']}* (conf {result['confidence']:.2f})")
    lines.append(f"Action: `{result['action_taken']}`")
    if result.get("referral_name") or result.get("referral_email"):
        lines.append(
            f"🔁 *Referral:* {result.get('referral_name') or '?'} "
            f"<{result.get('referral_email') or '?'}>"
        )
    if result.get("mentioned_competitor"):
        lines.append(f"🆚 Competitor mentioned: *{result['mentioned_competitor']}*")
    if result.get("requeue_date"):
        lines.append(f"📅 Requeue: {result['requeue_date']}")
    if result.get("reasoning"):
        lines.append(f"_💭 {result['reasoning'][:200]}_")
    if reply_text:
        lines.append("Reply:\n```" + reply_text[:400] + "```")
    return "\n".join(lines)


async def _classify_and_notify(activity_id: str, row: dict) -> None:
    """Background task: classify a freshly-arrived ABM v2 reply, persist the
    verdict to reply_classifications, and post a formatted alert to Slack.

    Runs out-of-band so the webhook response stays fast (Lemlist may retry
    on slow responses).
    """
    # Defer imports — keeps webhook startup cheap and avoids Anthropic SDK
    # import cost on non-reply events.
    from pipelines.reply_intelligence import classify_reply, extract_new_reply
    from utils.slack import notify

    payload = row.get("raw_payload") or {}
    full_text = payload.get("text") or payload.get("messagePreview") or ""
    reply_text = extract_new_reply(full_text)
    subject = payload.get("subject") or ""
    sender_email = payload.get("fromEmail") or row.get("lead_email") or ""

    try:
        result = await classify_reply(reply_text, subject, sender_email)
    except Exception:
        logger.exception("reply_classifier: error for %s", row.get("lead_email"))
        await notify(
            f"⚠️ Reply classification ERROR for `{row.get('lead_email')}` "
            f"({row.get('company_name')}). Manual review needed.",
            success=False,
        )
        return

    if not result:
        await notify(
            f"⚠️ Reply classification returned no verdict for `{row.get('lead_email')}` "
            f"({row.get('company_name')}). Manual review needed.",
            success=False,
        )
        return

    # Persist the verdict (idempotent via lemlist_activity_id unique index)
    try:
        get_supabase().table("reply_classifications").insert({
            "lemlist_activity_id":  activity_id,
            "contact_email":        row.get("lead_email") or sender_email,
            "domain":               row.get("domain") or payload.get("companyDomain"),
            "company_name":         row.get("company_name") or payload.get("leadCompanyName"),
            "campaign_id":          row.get("campaign_id"),
            "campaign_name":        row.get("campaign_name"),
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
    except Exception:
        logger.exception("reply_classifier: persist failed for %s", row.get("lead_email"))
        # continue to Slack anyway — operator should still see the verdict

    msg = _format_slack_message(row, subject, reply_text, result)
    # Treat anything except hard-negative classifications as "success" colour
    # so the alert doesn't accidentally turn red for positive replies.
    await notify(msg, success=not result["classification"].startswith("negative_"))


@router.post("/webhooks/lemlist")
async def receive_lemlist_event(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    _validate_secret(body)

    row = _parse_activity(body)
    logger.info("lemlist_event type=%s domain=%s", row["event_type"], row["domain"])

    insert_resp = get_supabase().table("lemlist_activities").insert(row).execute()
    activity_id = (insert_resp.data or [{}])[0].get("id")

    # Real-time reply classification + Slack alert — fires only on ABM v2 replies
    # so we don't classify (and notify) the wider Brevo Lemlist firehose.
    if (
        row.get("event_type") == "emailsReplied"
        and row.get("campaign_id") == _ABM_CAMPAIGN_ID
        and activity_id
    ):
        background_tasks.add_task(_classify_and_notify, activity_id, row)

    return {"status": "ok"}
