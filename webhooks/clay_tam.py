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
        "domain":         row.domain,
        "market":         row.market(),
        "company_name":   row.name,
        "company_type":   row.company_type,
        "employee_range": row.size,
        "location":       row.location,
        "country":        row.country,
        "linkedin_url":   row.linkedin_url,
        "vertical":       row.vertical,
        "clay_id":        row.clay_id,
        "raw":            row.model_dump(by_alias=True),
    }


def _upsert_in_chunks(rows: list[dict], chunk_size: int = 100) -> None:
    sb = get_supabase()
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        sb.table("sourced_tam_v2").upsert(chunk, on_conflict="domain,market,company_name").execute()
        logger.info("clay_tam: upserted rows %d-%d", i, i + len(chunk))
    logger.info("clay_tam: total accepted %d", len(rows))


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
    _upsert_in_chunks(rows)

    return {"status": "ok", "accepted": len(rows)}
