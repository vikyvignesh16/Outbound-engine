import hmac
import logging
import os

from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import ValidationError

from db.client import get_supabase
from db.models import ClayContactWebhookPayload
from utils.linkedin import normalise_linkedin_url

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_secret(secret: str | None) -> None:
    """Static shared-secret check, fails closed. Deliberately a plain header
    compare (not an HMAC body signature like clay_tam.py) because Clay's
    no-code webhook action can attach a fixed header value but can't easily
    compute a per-request signature.
    """
    expected = os.environ.get("CLAY_CONTACTS_WEBHOOK_SECRET")
    if not expected or not hmac.compare_digest(secret or "", expected):
        raise HTTPException(status_code=401, detail="invalid or missing X-Clay-Contacts-Secret")


def _resolve_batch_number(sb, contact: ClayContactWebhookPayload) -> int | None:
    """Returns batch_number from payload, or falls back to campaign_batches lookup."""
    if contact.batch_number is not None:
        return contact.batch_number
    row = (
        sb.table("campaign_batches")
        .select("batch_number")
        .eq("domain", contact.domain)
        .eq("market", contact.market)
        .limit(1)
        .execute()
        .data
    )
    return row[0]["batch_number"] if row else None


def _transform(contact: ClayContactWebhookPayload, batch_number: int | None, raw_body: dict) -> dict:
    return {
        "domain":              contact.domain,
        "email":               contact.email,
        "first_name":          contact.first_name,
        "last_name":           contact.last_name,
        "job_title":           contact.job_title,
        "seniority":           contact.seniority,
        "linkedin_url":        normalise_linkedin_url(contact.linkedin_url),
        "company_name":        contact.company_name,
        "market":              contact.market,
        "batch_number":        batch_number,
        "source":              "clay",
        "relevance_score":     contact.relevance_score,
        "relevance_reasoning": contact.relevance_reasoning,
        "raw": {
            "location": contact.location or "",
            "country": contact.country or "",
            "clay_full_payload": raw_body,
        },
    }


@router.post("/webhooks/clay/contacts")
async def receive_clay_contact(
    request: Request,
    x_clay_contacts_secret: str | None = Header(None),
):
    _validate_secret(x_clay_contacts_secret)

    raw_body = await request.json()
    try:
        contact = ClayContactWebhookPayload.model_validate(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    if not normalise_linkedin_url(contact.linkedin_url):
        raise HTTPException(status_code=422, detail="linkedin_url is required and must be non-empty")

    sb = get_supabase()
    row = _transform(contact, _resolve_batch_number(sb, contact), raw_body)
    sb.table("sourced_contacts").upsert(row, on_conflict="linkedin_url").execute()

    logger.info("clay_contacts: upserted contact for domain=%s market=%s", contact.domain, contact.market)
    return {"status": "ok", "inserted": 1}
