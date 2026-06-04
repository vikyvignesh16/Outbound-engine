import logging

from fastapi import APIRouter, Request

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhooks/albacross")
async def receive_albacross_event(request: Request):
    body = await request.json()
    logger.info("albacross_event: %s", body)
    get_supabase().table("albacross_signals").insert({"raw_payload": body}).execute()
    return {"status": "ok"}
