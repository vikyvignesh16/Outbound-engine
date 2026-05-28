import hmac
import hashlib
import os
import logging

from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import ValidationError

from db.client import get_supabase
from db.models import ClayContactRow, ClayContactsPayload

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_signature(raw_body: bytes, signature: str | None, secret_env: str) -> None:
    secret = os.environ.get(secret_env, "")
    if not secret:
        return
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _resolve_batch_number(sb, contact: ClayContactRow) -> int | None:
    """Returns batch_number from payload, or falls back to campaign_batches lookup."""
    if contact.batch_number is not None:
        return contact.batch_number
    if not contact.domain:
        return None
    query = sb.table("campaign_batches").select("batch_number").eq("domain", contact.domain)
    if contact.market:
        query = query.eq("market", contact.market)
    row = query.limit(1).execute().data
    return row[0]["batch_number"] if row else None


def _transform_row(contact: ClayContactRow, batch_number: int | None) -> dict:
    return {
        "domain":       contact.domain,
        "email":        contact.email,
        "first_name":   contact.first_name,
        "last_name":    contact.last_name,
        "job_title":    contact.job_title,
        "seniority":    contact.seniority,
        "linkedin_url": contact.linkedin_url,
        "company_name": contact.company_name,
        "market":       contact.market,
        "batch_number": batch_number,
        "raw":          contact.model_dump(),
    }


def _upsert_in_chunks(rows: list[dict], chunk_size: int = 100) -> None:
    sb = get_supabase()
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        sb.table("sourced_contacts").upsert(chunk, on_conflict="domain,email").execute()
    logger.info("clay_contacts: upserted %d contacts", len(rows))


@router.post("/webhooks/clay/contacts")
async def receive_clay_contacts(
    request: Request,
    x_clay_signature: str | None = Header(None),
):
    raw_body = await request.body()
    _validate_signature(raw_body, x_clay_signature, "CLAY_WEBHOOK_SECRET")

    try:
        payload = ClayContactsPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    sb = get_supabase()
    rows = [_transform_row(c, _resolve_batch_number(sb, c)) for c in payload.rows]
    _upsert_in_chunks(rows)

    return {"status": "ok", "accepted": len(rows)}
