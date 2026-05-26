# Brevo Outbound Engine — Skill Reference

## Purpose
Reusable code patterns for the Brevo outbound engine.
Read this before writing any new endpoint, transformer, or pipeline.
Every file in this project follows these patterns exactly.

---

## 1. FastAPI app setup

```python
# api/main.py
from fastapi import FastAPI
from webhooks import clay_tam, albacross, lemlist, clay_contacts
from pipelines import qualification, enrichment, monthly_batch
from routing import router

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)
app.include_router(albacross.router)
app.include_router(lemlist.router)
app.include_router(clay_contacts.router)
app.include_router(qualification.router)
app.include_router(enrichment.router)
app.include_router(monthly_batch.router)
app.include_router(router.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

---

## 2. Database client pattern

```python
# db/client.py
from supabase import create_client
import asyncpg
import os

# supabase-py — use for simple single-table reads/writes
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

# asyncpg — use for complex joins, multi-table ops, raw SQL
async def get_pg():
    return await asyncpg.connect(os.environ["SUPABASE_DB_URL"])
```

**Rule:** Use `supabase` for single-table CRUD.
Use `get_pg()` for joins, transactions, or anything needing raw SQL.

---

## 3. Webhook endpoint pattern

Every webhook follows this exact structure:
1. Read raw body
2. Validate signature
3. Parse into Pydantic model
4. Transform to internal schema
5. Write to Supabase
6. Return status

```python
from fastapi import APIRouter, Request, Header, HTTPException
from db.client import supabase
from db.models import ClayTAMPayload
import hmac, hashlib, os

router = APIRouter()

def validate_signature(raw_body: bytes, signature: str, secret_env: str) -> None:
    """Reusable signature validator. Raises 401 if invalid."""
    expected = hmac.new(
        os.environ[secret_env].encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/webhooks/clay/tam")
async def receive_clay_tam(
    request: Request,
    x_clay_signature: str = Header(None)
):
    raw_body = await request.body()
    validate_signature(raw_body, x_clay_signature, "CLAY_WEBHOOK_SECRET")
    payload = ClayTAMPayload.model_validate_json(raw_body)
    rows = [_transform_row(row, payload.run_id) for row in payload.rows]
    supabase.table("sourced_tam").upsert(
        rows, on_conflict="domain,market"
    ).execute()
    return {"status": "ok", "inserted": len(rows)}

def _transform_row(row, run_id: str) -> dict:
    """
    ⚠️ Field names are placeholders — update when real Clay payload confirmed.
    """
    return {
        "domain": row.domain,
        "company_name": row.company_name,
        "market": row.market,
        "employee_count": row.employee_count,
        "industry": row.industry,
        "clay_run_id": run_id,
        "raw": row.model_dump()
    }
```

---

## 4. Pydantic models

All models live in `db/models.py`.
Fields marked ⚠️ are placeholders — update when real payloads confirmed.

```python
# db/models.py
from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime

# ── Clay TAM ──────────────────────────────────────────────
class ClayTAMRow(BaseModel):
    # ⚠️ PENDING: update field names from real Clay payload
    domain: str
    company_name: Optional[str] = None
    market: str                          # FR | UK | US | DE
    employee_count: Optional[int] = None
    industry: Optional[str] = None

class ClayTAMPayload(BaseModel):
    run_id: str
    rows: List[ClayTAMRow]

# ── Clay Contacts ──────────────────────────────────────────
class ClayContactRow(BaseModel):
    # ⚠️ PENDING: update field names from real Clay contacts payload
    domain: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None

class ClayContactsPayload(BaseModel):
    run_id: str
    rows: List[ClayContactRow]

# ── Albacross ──────────────────────────────────────────────
class AlbacrossPayload(BaseModel):
    # ⚠️ PENDING: update field names from real Albacross payload
    domain: str
    occurred_at: datetime
    raw_data: Any = None

# ── Lemlist ────────────────────────────────────────────────
class LemlistPayload(BaseModel):
    # ⚠️ PENDING: update field names from real Lemlist payload
    email: str
    event_type: str
    occurred_at: datetime
    raw_data: Any = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        allowed = {"email_open", "email_click", "reply", "bounce", "unsubscribe"}
        if v not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v
```

---

## 5. Albacross transformer pattern

Pure function — raw dict in, clean jsonb dict out.
Runs between webhook receiver and Supabase write.
⚠️ Update field names once real Albacross payload confirmed.

```python
# webhooks/albacross_transformer.py

def transform_albacross_payload(raw: dict) -> dict:
    return {
        "visit": {
            "page_url": raw.get("pageUrl"),
            "duration_seconds": raw.get("visitDuration"),
            "pages_viewed": raw.get("pagesViewed"),
            "referrer": raw.get("referrer")
        },
        "firmographics": {
            "industry": raw.get("industry"),
            "employee_range": raw.get("employeeRange"),
            "country": raw.get("country"),
            "revenue_range": raw.get("revenueRange")
        },
        "session": {
            "first_visit": raw.get("isFirstVisit"),
            "visit_count": raw.get("visitCount"),
            "last_seen": raw.get("lastSeen")
        }
    }

def extract_domain_from_albacross(raw: dict) -> str:
    """⚠️ Field name is a placeholder — update from real payload."""
    return raw.get("companyDomain") or raw.get("domain") or ""
```

---

## 6. Lemlist transformer pattern

Handles all event types. Extracts domain from contact email.
⚠️ Update field names once real Lemlist payload confirmed.

```python
def transform_lemlist_payload(raw: dict, event_type: str) -> dict:
    base = {
        "campaign": {
            "id": raw.get("campaignId"),
            "name": raw.get("campaignName"),
            "step": raw.get("sequenceStep")
        },
        "lead": {
            "lemlist_id": raw.get("leadId"),
            "first_name": raw.get("firstName"),
            "last_name": raw.get("lastName")
        }
    }
    if event_type == "email_click":
        base["engagement"] = {
            "clicked_url": raw.get("clickedUrl"),
            "device": raw.get("device")
        }
    elif event_type == "reply":
        base["engagement"] = {
            "reply_text": raw.get("replyText"),
            "sentiment": raw.get("sentiment")
        }
    return base

def extract_domain_from_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@")[1].lower().strip()
```

---

## 7. Monthly batch selection query

```python
# pipelines/monthly_batch.py

BATCH_SELECTION_QUERY = """
    SELECT domain, market, company_name, account_fit_score, vertical
    FROM sourced_tam
    WHERE account_fit_score >= 3
    AND domain NOT IN (
        SELECT domain FROM campaign_batches
    )
    ORDER BY account_fit_score DESC, created_at ASC
    LIMIT $1;
"""

async def select_next_batch(limit: int = 1000) -> list:
    """
    Selects next N uncontacted companies with fit score >= 3.
    Sequential — no time window. Each run picks up where last left off.
    """
    conn = await get_pg()
    try:
        rows = await conn.fetch(BATCH_SELECTION_QUERY, limit)
        return [dict(row) for row in rows]
    finally:
        await conn.close()
```

---

## 8. Supabase upsert patterns

```python
# Single row upsert
supabase.table("sourced_tam").upsert(
    {"domain": "acme.com", "market": "FR", ...},
    on_conflict="domain,market"
).execute()

# Batch upsert
supabase.table("sourced_tam").upsert(
    rows,  # list of dicts
    on_conflict="domain,market"
).execute()

# Read with filters
response = supabase.table("sourced_tam")\
    .select("*")\
    .eq("market", "FR")\
    .gte("account_fit_score", 3)\
    .execute()

# Update status
supabase.table("contacts_sourced")\
    .update({"status": "enrolled"})\
    .eq("id", contact_id)\
    .execute()
```

---

## 9. Error handling pattern

```python
import logging
logger = logging.getLogger(__name__)

# Webhook errors — raise immediately
raise HTTPException(status_code=401, detail="Invalid signature")
raise HTTPException(status_code=422, detail="Missing required field: domain")
raise HTTPException(status_code=500, detail="Supabase write failed")

# Pipeline errors — catch per record, don't crash the batch
for company in companies:
    try:
        result = call_technographic_api(company["domain"])
    except Exception as e:
        logger.error(f"Technographic API failed for {company['domain']}: {e}")
        continue
```

---

## 10. dbt test patterns

```yaml
# dbt/models/tests/schema.yml
models:
  - name: sourced_tam
    columns:
      - name: domain
        tests:
          - not_null
      - name: market
        tests:
          - not_null
          - accepted_values:
              values: ['FR', 'UK', 'US', 'DE']
      - name: account_fit_score
        tests:
          - accepted_values:
              values: [1, 2, 3, 4, 5]

  - name: touchpoints
    columns:
      - name: source
        tests:
          - accepted_values:
              values: ['albacross', 'lemlist']
      - name: event_type
        tests:
          - accepted_values:
              values: ['visit', 'email_open', 'email_click',
                       'reply', 'bounce', 'unsubscribe']

  - name: contacts_sourced
    columns:
      - name: status
        tests:
          - accepted_values:
              values: ['new', 'enrolled', 'replied', 'disqualified']
      - name: domain
        tests:
          - relationships:
              to: ref('sourced_tam')
              field: domain
```

**Custom SQL test — routing must happen after sourcing:**
```sql
-- dbt/tests/assert_routing_after_sourcing.sql
select cr.id
from contacts_routed cr
left join contacts_sourced cs on cr.contact_id = cs.id
where cr.routed_at < cs.created_at
```

**Run dbt tests from pipeline:**
```python
import subprocess

def run_dbt_tests():
    result = subprocess.run(
        ["dbt", "test", "--profiles-dir", ".", "--target", "prod"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"dbt tests failed:\n{result.stdout}")
    return result.returncode
```

---

## 11. Open items — do not implement until confirmed

| Item | Affects |
|---|---|
| Clay TAM payload field names | `db/models.py` ClayTAMRow, `webhooks/clay_tam.py` |
| Clay market field location | `webhooks/clay_tam.py` normalisation logic |
| Albacross payload field names | `webhooks/albacross_transformer.py` |
| Lemlist payload field names | `db/models.py` LemlistPayload, `webhooks/lemlist.py` |
| Clay contacts payload field names | `db/models.py` ClayContactRow |
| Technographic API spec | `pipelines/qualification.py` |
| Qualification rules | `pipelines/qualification.py` rules engine |
| Rep list | `routing/router.py` round-robin logic |
| Lemlist campaign IDs per market + vertical | `routing/router.py` enrollment logic |
