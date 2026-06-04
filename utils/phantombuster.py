import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

PB_BASE = "https://api.phantombuster.com/api/v2"


def _headers() -> dict:
    return {"X-Phantombuster-Key": os.environ["PHANTOMBUSTER_API_KEY"]}


def launch_agent(agent_id: str, argument: dict) -> str:
    """Launch a PhantomBuster agent. Returns containerId."""
    with httpx.Client() as client:
        resp = client.post(
            f"{PB_BASE}/agents/launch",
            headers=_headers(),
            json={"id": agent_id, "argument": argument},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["containerId"]


def get_container(container_id: str) -> dict:
    """Fetch container status and output."""
    with httpx.Client() as client:
        resp = client.get(
            f"{PB_BASE}/containers/fetch",
            headers=_headers(),
            params={"id": container_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def is_finished(container: dict) -> bool:
    return container.get("status") in ("finished", "error", "stopped")


def is_error(container: dict) -> bool:
    return container.get("status") in ("error", "stopped")


def get_result_rows(container: dict) -> list[dict]:
    """Extract result rows from container resultObject (JSON string → list)."""
    raw = container.get("resultObject") or "[]"
    result = json.loads(raw) if isinstance(raw, str) else raw
    return result if isinstance(result, list) else []
