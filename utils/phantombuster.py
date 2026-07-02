import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

PB_BASE = "https://api.phantombuster.com/api/v2"

# Cache of saved agent arguments (sessionCookie, userAgent, etc.) keyed by agent_id.
# Refreshed on cache miss or when invalidate_saved_args() is called after a session-expired
# error.  Lives for the lifetime of the process — fine for our Railway long-running app.
_SAVED_ARGS_CACHE: dict[str, dict] = {}

# Output markers that PB writes when the LinkedIn session cookie is no longer valid.
_SESSION_EXPIRED_MARKERS = (
    "session cookie",
    "session expired",
    "expired cookie",
    "li_at",
    "not connected",
    "cookie is invalid",
)


def _headers() -> dict:
    return {"X-Phantombuster-Key": os.environ["PHANTOMBUSTER_API_KEY"]}


def _fetch_saved_argument(agent_id: str) -> dict:
    """GET /agents/fetch and return the parsed `argument` JSON saved on PB."""
    with httpx.Client() as client:
        resp = client.get(
            f"{PB_BASE}/agents/fetch",
            headers=_headers(),
            params={"id": agent_id},
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json().get("argument") or "{}"
        return json.loads(raw) if isinstance(raw, str) else raw


def get_saved_argument(agent_id: str) -> dict:
    """Return cached saved argument, fetching from PB on cache miss."""
    if agent_id not in _SAVED_ARGS_CACHE:
        _SAVED_ARGS_CACHE[agent_id] = _fetch_saved_argument(agent_id)
        logger.info("phantombuster: cached saved argument for agent %s", agent_id)
    return _SAVED_ARGS_CACHE[agent_id]


def invalidate_saved_argument(agent_id: str) -> None:
    """Clear the cache for an agent — call when session cookie has expired."""
    _SAVED_ARGS_CACHE.pop(agent_id, None)
    logger.info("phantombuster: invalidated saved argument cache for agent %s", agent_id)


def launch_agent(agent_id: str, argument: dict) -> str:
    """Launch a PB agent. Merges `argument` over the saved defaults (sessionCookie etc).
    Returns containerId."""
    merged = {**get_saved_argument(agent_id), **argument}
    with httpx.Client() as client:
        resp = client.post(
            f"{PB_BASE}/agents/launch",
            headers=_headers(),
            json={"id": agent_id, "argument": merged},
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


def _fetch_container_output(container_id: str) -> str:
    """Get the container's stdout/stderr log — used for S3 URL parsing + error detection."""
    with httpx.Client() as client:
        resp = client.get(
            f"{PB_BASE}/containers/fetch-output",
            headers=_headers(),
            params={"id": container_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("output", "") or ""


def get_result_rows(container: dict) -> list[dict]:
    """Extract result rows from a PB container.
    Tries `resultObject` first (inline JSON), then falls back to the result.json
    written to S3 by Phantom scripts that save their output to S3 instead of stdout."""
    raw = container.get("resultObject")
    if raw:
        try:
            result = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: fetch result.json from the container's S3 output log
    cid = container.get("id") or container.get("containerId")
    if not cid:
        return []
    output = _fetch_container_output(str(cid))
    json_url = _find_result_json_url(output)
    if not json_url:
        return []
    # PB S3 URLs can contain spaces from csvName ("Commercenext improved Audience.json").
    # HTTP-encode them so httpx accepts the URL and S3 can locate the object.
    from urllib.parse import quote
    safe_url = quote(json_url, safe=":/?#[]@!$&'()*+,;=%")
    try:
        with httpx.Client() as client:
            resp = client.get(safe_url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning("phantombuster: failed to fetch %s — %s", safe_url, exc)
        return []


def _find_result_json_url(output: str) -> str | None:
    """Parse PB stdout to find the JSON result S3 URL.

    Different PB agents save under different filenames:
      • Company Extractor          → {csvName}.json (with SPACES in csvName)
      • Sales Nav Search Export    → {csvName}.json (with SPACES in csvName)

    The marker we anchor on is the literal `JSON saved at <url>` line that all
    PB save-output scripts emit. We take the last such URL, extending it up to
    and including the .json extension — PB S3 URLs regularly contain spaces
    (from csvName templates like "Commercenext improved Audience.json"),
    so we CAN'T truncate on whitespace."""
    json_url = None
    for line in output.splitlines():
        if "JSON saved at" not in line:
            continue
        idx = line.find("https://")
        if idx < 0:
            continue
        rest = line[idx:].rstrip()  # keep interior spaces, drop trailing \r
        end = rest.rfind(".json")
        if end < 0:
            continue
        json_url = rest[:end + len(".json")]
    return json_url


def output_shows_scrape_success(container: dict) -> bool:
    """True when PB's stdout log shows the Company Extractor scrape completed.

    Actual markers observed in raw PB output (from the diagnose endpoint on
    2026-07-02 with Brevo's LinkedIn URL):
      [done_]✅ Scraped data for company Brevo.
      [done_]✅ JSON saved at https://phantombuster.s3.amazonaws.com/.../....json
      [done_]✅ Data successfully saved!
      * Process finished successfully (exit code: 0)

    Any of these confirm the scrape ran to completion. Callers can then leave
    a row in extracting_company to re-poll (in case resultObject / S3 fetch
    is still catching up) rather than burning a fresh PB launch.
    """
    cid = container.get("id") or container.get("containerId")
    if not cid:
        return False
    output = _fetch_container_output(str(cid))
    if not output:
        return False
    return (
        "Scraped data for company" in output or
        "JSON saved at" in output or
        "Data successfully saved" in output or
        "company was scraped" in output or       # keep old markers as safety net
        "companies were scraped" in output
    )


def session_expired(container: dict) -> bool:
    """Heuristic check: did this container fail because the LinkedIn session cookie expired?
    Reads the container output log and looks for known PB error markers."""
    cid = container.get("id") or container.get("containerId")
    if not cid:
        return False
    output = _fetch_container_output(str(cid)).lower()
    return any(marker in output for marker in _SESSION_EXPIRED_MARKERS) and is_error(container)
