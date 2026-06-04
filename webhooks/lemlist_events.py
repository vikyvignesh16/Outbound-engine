import logging
import os

from fastapi import APIRouter, Request, HTTPException
from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_secret(body: dict) -> None:
    """Lemlist sends the webhook secret inside the JSON body as a 'secret' field."""
    secret = os.environ.get("LEMLIST_WEBHOOK_SECRET", "")
    if not secret:
        return
    if body.get("secret") != secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


def _parse_activity(body: dict) -> dict:
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
        "raw_payload":   body,
    }


@router.post("/webhooks/lemlist")
async def receive_lemlist_event(request: Request):
    body = await request.json()
    _validate_secret(body)

    row = _parse_activity(body)
    logger.info("lemlist_event type=%s domain=%s", row["event_type"], row["domain"])

    get_supabase().table("lemlist_activities").insert(row).execute()

    return {"status": "ok"}
