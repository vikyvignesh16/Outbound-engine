"""Push priority_tam rows into Brevo CRM as Company records.

Routing per row:
  brevo_company_id present  → PATCH /v3/companies/{id}   (update)
  brevo_company_id missing  → POST  /v3/companies        (create)

Idempotent re-runs: after each successful call we write back two columns
to priority_tam:
  - brevo_company_id    (the new id returned by POST, if it was a create)
  - brevo_sync_method   ('POST' or 'PATCH')
So the next run sees the row as already-synced and routes it to PATCH
instead of CREATE — no duplicates in Brevo CRM.

Field mapping (priority_tam → Brevo CRM):
  company_name          → name (payload root)
  domain                → attributes.website
  location              → attributes.city (first comma segment only)
  country               → attributes.ent_country
  employee_range        → attributes.ent_number_of_employees_range (strip " employees")
  company_type          → attributes.ent_tam_company_type ("Privately Held"→"Private",
                                                            "Public Company"→"Public")
  esp_detected          → attributes.ent_tam_esp_detected
  vertical              → attributes.ent_tam_vertical (raw, pass through)
  linkedin_url          → attributes.linkedin
  has_wallet / needs_cdp / has_loyalty_program (bool flags)
                        → attributes.ent_tam_use_cases (array of names of TRUE flags;
                                                        field omitted if none true)
  current UTC at call   → attributes.ent_update_bypass_time ("YYYY-MM-DDTHH:mm")

Any attribute whose source column is NULL/empty is dropped from the payload.
"""
import asyncio
import logging
import os
from datetime import datetime, timezone

import httpx

from db.client import fetch_all, get_supabase

logger = logging.getLogger(__name__)

BREVO_CRM_BASE_URL = "https://api.brevo.com/v3"
_MAX_INFLIGHT = 5
_HTTP_TIMEOUT = 30.0


# ── Field-level transforms ────────────────────────────────────────────────────

def _clean_employee_range(val):
    if not val:
        return None
    s = str(val).strip()
    if s.lower().endswith(" employees"):
        s = s[: -len(" employees")].strip()
    return s or None


def _normalise_company_type(val):
    if not val:
        return None
    s = str(val).strip()
    return {"privately held": "Private", "public company": "Public"}.get(s.lower(), s) or None


def _first_city(val):
    if not val:
        return None
    return (str(val).split(",")[0].strip() or None)


def _build_use_cases(row):
    arr = []
    if row.get("has_wallet") is True:
        arr.append("has_wallet")
    if row.get("needs_cdp") is True:
        arr.append("needs_cdp")
    if row.get("has_loyalty_program") is True:
        arr.append("has_loyalty_program")
    return arr or None


def _now_bypass_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")


# ── Payload builder ───────────────────────────────────────────────────────────

def build_payload(row):
    """Map a priority_tam row to a Brevo CRM payload, dropping null/empty attrs."""
    attrs_raw = {
        "city":                          _first_city(row.get("location")),
        "ent_country":                   row.get("country"),
        "ent_number_of_employees_range": _clean_employee_range(row.get("employee_range")),
        "ent_tam_company_type":          _normalise_company_type(row.get("company_type")),
        "ent_tam_esp_detected":          row.get("esp_detected"),
        "ent_tam_use_cases":             _build_use_cases(row),
        "ent_tam_vertical":              row.get("vertical"),
        "linkedin":                      row.get("linkedin_url"),
        "website":                       row.get("domain"),
        "ent_update_bypass_time":        _now_bypass_time(),
    }
    attributes = {k: v for k, v in attrs_raw.items() if v not in (None, "", [], {})}
    payload = {"attributes": attributes}
    if row.get("company_name"):
        payload["name"] = row["company_name"]
    return payload


# ── HTTP layer ────────────────────────────────────────────────────────────────

def _headers():
    return {
        "api-key": os.environ["BREVO_CRM_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _patch_company(client, brevo_id, payload):
    return await client.patch(
        f"{BREVO_CRM_BASE_URL}/companies/{brevo_id}",
        headers=_headers(),
        json=payload,
    )


async def _post_company(client, payload):
    return await client.post(
        f"{BREVO_CRM_BASE_URL}/companies",
        headers=_headers(),
        json=payload,
    )


def _writeback_after_sync(row_id, method, new_brevo_id=None):
    """Mark a priority_tam row as synced. Failure to write back is logged
    but does NOT roll back the successful CRM call."""
    update = {"brevo_sync_method": method}
    if new_brevo_id:
        update["brevo_company_id"] = new_brevo_id
    try:
        get_supabase().table("priority_tam").update(update).eq("id", row_id).execute()
    except Exception:
        logger.exception("crm_sync: writeback failed for row %s (method=%s, new_id=%s)",
                         row_id, method, new_brevo_id)


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def sync_priority_tam_to_crm(market_filter=None, limit=None, dry_run=False,
                                   update_limit=None, create_limit=None):
    """One-shot push of priority_tam → Brevo CRM.

    Returns a status dict with updated/created/failed counts and a sample of
    failures (first 50) for the operator to inspect.

    update_limit / create_limit cap the rows processed per mode after fetching —
    useful for smoke tests (e.g. update_limit=100, create_limit=100 → 200 rows
    total split evenly between PATCH and POST paths).
    """
    filters = [("eq", "market", market_filter)] if market_filter else None
    rows = fetch_all(
        "priority_tam",
        ("id, domain, market, company_name, brevo_company_id, vertical, esp_detected, "
         "company_type, employee_range, location, country, linkedin_url, "
         "has_wallet, has_loyalty_program, needs_cdp"),
        filters=filters,
        limit=limit,
    )

    if update_limit is not None or create_limit is not None:
        update_rows = [r for r in rows if (r.get("brevo_company_id") or "").strip()]
        create_rows = [r for r in rows if not (r.get("brevo_company_id") or "").strip()]
        if update_limit is not None:
            update_rows = update_rows[:update_limit]
        if create_limit is not None:
            create_rows = create_rows[:create_limit]
        rows = update_rows + create_rows

    update_n = sum(1 for r in rows if (r.get("brevo_company_id") or "").strip())
    create_n = len(rows) - update_n
    logger.info("crm_sync: %d rows (%d update, %d create) dry_run=%s",
                len(rows), update_n, create_n, dry_run)

    if dry_run:
        sample_n = min(5, len(rows))
        for i, r in enumerate(rows[:sample_n]):
            payload = build_payload(r)
            mode = "PATCH" if (r.get("brevo_company_id") or "").strip() else "POST"
            logger.info("DRYRUN [%d/%d] %s %s  attrs=%s",
                        i + 1, sample_n, mode, r.get("domain"),
                        sorted(payload.get("attributes", {}).keys()))
        return {"status": "dry_run", "total": len(rows),
                "would_update": update_n, "would_create": create_n}

    sem = asyncio.Semaphore(_MAX_INFLIGHT)
    updated = 0
    created = 0
    failed = 0
    failures = []

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        async def _one(row):
            nonlocal updated, created, failed
            async with sem:
                payload = build_payload(row)
                brevo_id = (row.get("brevo_company_id") or "").strip()
                mode = "PATCH" if brevo_id else "POST"
                try:
                    if brevo_id:
                        resp = await _patch_company(client, brevo_id, payload)
                        if resp.status_code == 204:
                            updated += 1
                            _writeback_after_sync(row["id"], "PATCH")
                            return
                    else:
                        resp = await _post_company(client, payload)
                        if resp.status_code in (200, 201):
                            created += 1
                            new_id = (resp.json() or {}).get("id")
                            _writeback_after_sync(row["id"], "POST", new_brevo_id=new_id)
                            return
                    failed += 1
                    failures.append({
                        "domain": row.get("domain"), "mode": mode,
                        "status": resp.status_code, "body": resp.text[:300],
                    })
                except Exception as exc:
                    failed += 1
                    failures.append({
                        "domain": row.get("domain"), "mode": mode,
                        "status": "exception", "body": str(exc)[:300],
                    })

                done = updated + created + failed
                if done % 100 == 0:
                    logger.info("crm_sync progress: %d/%d (updated=%d created=%d failed=%d)",
                                done, len(rows), updated, created, failed)

        await asyncio.gather(*[_one(r) for r in rows])

    logger.info("crm_sync done: updated=%d created=%d failed=%d",
                updated, created, failed)
    return {
        "status":   "ok",
        "total":    len(rows),
        "updated":  updated,
        "created":  created,
        "failed":   failed,
        "failures": failures[:50],
    }
