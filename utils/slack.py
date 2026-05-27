import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def notify(text: str, *, success: bool = True) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return
    color = "#36a64f" if success else "#d00000"
    payload = {"attachments": [{"color": color, "text": text, "mrkdwn_in": ["text"]}]}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5.0)
    except Exception as exc:
        logger.warning("slack: notify failed: %s", exc)
