import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

# Albacross sends ISO country codes. Most match our market codes except GB → UK.
_ISO_TO_MARKET: dict[str, str] = {"GB": "UK"}


def _iso_to_market(iso: str | None) -> str | None:
    if not iso:
        return None
    return _ISO_TO_MARKET.get(iso, iso)


def _ms_to_iso(ms: int | None) -> str | None:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def _parse_signal(body: dict) -> dict:
    country = body.get("country")
    return {
        "domain":            body.get("website"),
        "company_name":      body.get("name"),
        "country":           country,
        "market":            _iso_to_market(country),
        "pages_high_intent": body.get("pages_high_intent"),
        "pages_visited":     body.get("pages_visited"),
        "visits":            body.get("visits"),
        "unique_7_days":     body.get("unique_pages_visited_7_days"),
        "unique_30_days":    body.get("unique_pages_visited_30_days"),
        "unique_90_days":    body.get("unique_pages_visited_90_days"),
        "last_visit":        _ms_to_iso(body.get("last_visit")),
        "duration":          body.get("duration"),
        "segment_name":      body.get("segment_name"),
        "utms":              body.get("utms"),
        "raw_payload":       body,
    }


@router.post("/webhooks/albacross")
async def receive_albacross_event(request: Request):
    body = await request.json()
    row = _parse_signal(body)
    logger.info("albacross_event: domain=%s market=%s segment=%s",
                row["domain"], row["market"], row["segment_name"])
    get_supabase().table("albacross_signals").insert(row).execute()
    return {"status": "ok"}
