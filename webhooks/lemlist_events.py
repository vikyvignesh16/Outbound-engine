import logging
import os

from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_secret(body: dict) -> None:
    """Lemlist sends the webhook secret inside the JSON body as a 'secret' field."""
    secret = os.environ.get("LEMLIST_WEBHOOK_SECRET", "")
    if not secret:
        return
    if body.get("secret") != secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


@router.post("/webhooks/lemlist")
async def receive_lemlist_event(request: Request):
    body = await request.json()
    _validate_secret(body)
    logger.info("lemlist_event: %s", body)
    return {"status": "ok"}
