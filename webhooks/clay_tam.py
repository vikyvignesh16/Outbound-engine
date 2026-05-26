import hmac
import hashlib
import os
import logging

from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import ValidationError
from db.client import get_supabase
from db.models import ClayTAMRow, ClayTAMPayload

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_signature(raw_body: bytes, signature: str | None, secret_env: str) -> None:
    """Raises 401 if the HMAC-SHA256 signature does not match."""
    secret = os.environ.get(secret_env, "")
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _transform_row(row: ClayTAMRow) -> dict:
    return {
        "domain":           row.domain,
        "market":           row.market(),
        "company_name":     row.name,
        "company_type":     row.company_type,
        "employee_range":   row.size,
        "location":         row.location,
        "country":          row.country,
        "linkedin_url":     row.linkedin_url,
        "brevo_company_id": row.brevo_company_id or None,
        "open_deals":       row.open_deals,
        "deal_lost_date":   str(row.deal_lost_date) if row.deal_lost_date else None,
        "vertical":         row.vertical,
        "clay_id":          row.clay_id,
        "raw":              row.model_dump(by_alias=True),
    }


@router.post("/webhooks/clay/tam")
async def receive_clay_tam(
    request: Request,
    x_clay_signature: str | None = Header(None),
):
    raw_body = await request.body()
    validate_signature(raw_body, x_clay_signature, "CLAY_WEBHOOK_SECRET")

    try:
        payload = ClayTAMPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    rows = [_transform_row(r) for r in payload.root]

    get_supabase().table("sourced_tam").upsert(rows, on_conflict="domain,market").execute()

    logger.info("clay_tam: upserted %d rows", len(rows))
    return {"status": "ok", "inserted": len(rows)}
