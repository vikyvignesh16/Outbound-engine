# Brevo Outbound Engine — Skill Reference

## Purpose
Real, current code patterns from this codebase. Every example below is
copied or lightly trimmed from an actual file (path given above each block),
not an aspirational placeholder — grep the path if you want the full context.
Read this before writing any new endpoint, transformer, or pipeline.

---

## 1. FastAPI app setup

```python
# api/main.py
import logging
from fastapi import FastAPI
from webhooks import clay_tam, clay_contacts, lemlist_events, albacross
from pipelines import (
    qualification, enrichment, monthly_batch, daily_runner, content,
    contact_gaps, score_contacts, domain_quality, linkedin_url_recovery,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

app = FastAPI(title="Brevo Outbound Engine")

app.include_router(clay_tam.router)
app.include_router(clay_contacts.router)
app.include_router(lemlist_events.router)
app.include_router(albacross.router)
app.include_router(qualification.router)
app.include_router(enrichment.router)
app.include_router(monthly_batch.router)
app.include_router(daily_runner.router)
app.include_router(content.router)
app.include_router(contact_gaps.router)
app.include_router(score_contacts.router)
app.include_router(domain_quality.router)
app.include_router(linkedin_url_recovery.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

Not every pipeline file gets a router — `crm_sync.py`, `dbt_runner.py`,
`reply_intelligence.py`, `news_search.py`, `lp_generator.py`, `resource_tool.py`
are library modules imported by other pipelines or run via `scripts/`, and are
never `include_router`'d here.

---

## 2. Database client pattern

```python
# db/client.py
from supabase import create_client, Client
import os

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _supabase

def fetch_all(
    table: str,
    select: str,
    filters: list | None = None,
    limit: int | None = None,
    order_by: list[tuple[str, bool]] | None = None,
) -> list[dict]:
    """Paginate through rows using .range(). Pass limit to cap total rows.
    order_by: list of (column, desc) tuples.

    PostgREST does not guarantee stable row order across separate paginated
    requests without an explicit ORDER BY — over many pages this can silently
    skip or duplicate rows between fetches. Always appends an "id" tiebreaker
    (unless already present) so pagination is deterministic even when the
    caller's sort column has ties (e.g. account_fit_score, prioritized_at).
    """
    sb = get_supabase()
    all_rows: list[dict] = []
    page_size = 1000
    offset = 0
    effective_order_by = order_by or [("id", False)]
    if order_by and not any(col == "id" for col, _ in order_by):
        effective_order_by = [*order_by, ("id", False)]
    while True:
        remaining = (limit - len(all_rows)) if limit else page_size
        batch_size = min(page_size, remaining)
        query = sb.table(table).select(select).range(offset, offset + batch_size - 1)
        if filters:
            for method, *args in filters:
                query = getattr(query, method)(*args)
        for col, desc in effective_order_by:
            query = query.order(col, desc=desc)
        batch = query.execute().data
        all_rows.extend(batch)
        if len(batch) < batch_size or (limit and len(all_rows) >= limit):
            break
        offset += batch_size
    return all_rows
```

There is no `asyncpg` connection anywhere in this codebase — everything goes
through `supabase-py`. `fetch_all` is the standard way to read more than a
page's worth of rows; a raw `sb.table(...).select(...).execute()` is fine for
single-page reads (below ~1000 rows) or writes.

---

## 3. Webhook patterns — three different auth mechanisms, by design

This codebase has three genuinely different webhook auth patterns, not one
canonical one. Check which one a given source actually needs before copying.

### 3a. HMAC-SHA256 body signature, fail-open if unset
```python
# webhooks/clay_tam.py
import hmac, hashlib, os
from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import ValidationError
from db.client import get_supabase
from db.models import ClayTAMRow, ClayTAMPayload

router = APIRouter()

def validate_signature(raw_body: bytes, signature: str | None, secret_env: str) -> None:
    """Raises 401 if the HMAC-SHA256 signature does not match.
    If the secret env var is not set, validation is skipped."""
    secret = os.environ.get(secret_env, "")
    if not secret:
        return
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

def _upsert_in_chunks(rows: list[dict], chunk_size: int = 100) -> None:
    sb = get_supabase()
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        sb.table("sourced_tam_v2").upsert(chunk, on_conflict="domain,market,company_name").execute()

@router.post("/webhooks/clay/tam")
async def receive_clay_tam(request: Request, x_clay_signature: str | None = Header(None)):
    raw_body = await request.body()
    validate_signature(raw_body, x_clay_signature, "CLAY_WEBHOOK_SECRET")
    try:
        payload = ClayTAMPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    rows = [_transform_row(r) for r in payload.root]
    _upsert_in_chunks(rows)
    return {"status": "ok", "accepted": len(rows)}
```

### 3b. Static shared-secret header, fail-closed
```python
# webhooks/clay_contacts.py
import hmac, os
from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import ValidationError
from db.client import get_supabase
from db.models import ClayContactWebhookPayload
from utils.linkedin import normalise_linkedin_url

router = APIRouter()

def _validate_secret(secret: str | None) -> None:
    """Static shared-secret check, fails closed. Deliberately a plain header
    compare (not an HMAC body signature) because Clay's no-code webhook
    action can attach a fixed header value but can't compute a per-request
    signature."""
    expected = os.environ.get("CLAY_CONTACTS_WEBHOOK_SECRET")
    if not expected or not hmac.compare_digest(secret or "", expected):
        raise HTTPException(status_code=401, detail="invalid or missing X-Clay-Contacts-Secret")

def _resolve_batch_number(sb, contact: ClayContactWebhookPayload) -> int | None:
    """Returns batch_number from payload, or falls back to a campaign_batches lookup."""
    if contact.batch_number is not None:
        return contact.batch_number
    row = (sb.table("campaign_batches").select("batch_number")
           .eq("domain", contact.domain).eq("market", contact.market)
           .limit(1).execute().data)
    return row[0]["batch_number"] if row else None

@router.post("/webhooks/clay/contacts")
async def receive_clay_contact(request: Request, x_clay_contacts_secret: str | None = Header(None)):
    _validate_secret(x_clay_contacts_secret)
    raw_body = await request.json()
    try:
        contact = ClayContactWebhookPayload.model_validate(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    if not normalise_linkedin_url(contact.linkedin_url):
        raise HTTPException(status_code=422, detail="linkedin_url is required and must be non-empty")
    sb = get_supabase()
    row = _transform(contact, _resolve_batch_number(sb, contact), raw_body)
    sb.table("sourced_contacts").upsert(row, on_conflict="linkedin_url").execute()
    return {"status": "ok", "inserted": 1}
```

### 3c. No auth + BackgroundTask insert (accept fast, write async)
```python
# webhooks/albacross.py (pattern, trimmed)
from fastapi import APIRouter, BackgroundTasks, Request

router = APIRouter()

async def _insert_signal(row: dict) -> None:
    """Runs after the response is sent. Swallows exceptions — Albacross's
    webhook client times out under ~1s and a synchronous insert (~700-900ms)
    was dropping ~5% of events to 499s before this was made async."""
    try:
        get_supabase().table("albacross_signals").insert(row).execute()
    except Exception:
        logger.exception("albacross: insert failed")

@router.post("/webhooks/albacross")
async def receive_albacross(request: Request, background_tasks: BackgroundTasks):
    raw = await request.json()
    row = _parse_signal(raw)
    background_tasks.add_task(_insert_signal, row)
    return {"status": "ok"}
```

**Takeaway:** don't assume a new webhook needs HMAC just because one existing
one has it. Match the auth mechanism to what the actual source system can do
(a no-code tool like Clay's webhook action can't compute a signature; a
first-party system you control can).

---

## 4. Pydantic models — real payload shapes

```python
# db/models.py
from pydantic import BaseModel, Field, RootModel
from typing import Optional, List

# ── Clay TAM — array payload, PascalCase aliases from Clay's export ─────────
class ClayTAMRow(BaseModel):
    model_config = {"populate_by_name": True}

    name: str                   = Field(alias="Name")
    company_type: Optional[str] = Field(None, alias="Type")
    size: Optional[str]         = Field(None, alias="Size")
    location: Optional[str]     = Field(None, alias="Location")
    country: Optional[str]      = Field(None, alias="Country")
    linkedin_url: Optional[str] = Field(None, alias="LinkedIn URL")
    domain: str                 = Field(alias="Domain")
    vertical: Optional[str]     = Field(None, alias="Primary Industry")

    def market(self) -> str:
        """market is derived from country, never sent directly by Clay."""
        return COUNTRY_TO_MARKET.get((self.country or "").lower(), self.country or "UNKNOWN")

class ClayTAMPayload(RootModel[List[ClayTAMRow]]):
    pass

# ── Clay Contacts — ONE object per call, not a batch array ──────────────────
class ClayContactWebhookPayload(BaseModel):
    """One contact per webhook call — Clay's 'send to webhook' action fires
    once per row. Field names match sourced_contacts columns directly."""
    domain: str
    linkedin_url: str
    market: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    seniority: Optional[str] = None
    relevance_score: Optional[int] = None
    relevance_reasoning: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    batch_number: Optional[int] = None
```

Lemlist and Albacross deliberately have **no Pydantic model** — both webhooks
parse the raw JSON dict directly (`_parse_activity()` / `_parse_signal()`),
because their payloads are wide, source-controlled event streams where a
strict schema would just mean constant maintenance for fields the pipeline
doesn't use. Reach for a Pydantic model when you control the sender's schema
(Clay's exports are stable and you configure them) — skip it for third-party
event firehoses.

---

## 5. BackgroundTasks pattern for long-running endpoints

Railway's edge proxy times out well before a multi-minute batch job (news +
LP prefetch, polling hundreds of Claude Batch results) finishes. Running that
work inline in the request handler causes a generic "upstream error" client
response even when the server-side work either succeeds or silently fails.
The fix, applied identically in two places (`content.py`'s `/submit` and
`/content-complete-all`):

```python
# pipelines/content.py
from fastapi import APIRouter, BackgroundTasks
from utils.slack import notify

async def _submit_content_bg(limit: int | None, markets: set[str] | None) -> None:
    try:
        result = await submit_content(limit=limit, markets=markets)
        await notify(f"✅ *Content generation submitted*\n• Contacts: {result['submitted']}")
    except Exception as exc:
        logger.exception("content_submit: background task failed")
        await notify(f"❌ *Content generation submission failed* — `{exc}`", success=False)

@router.post("/pipelines/content/submit")
async def content_submit(background_tasks: BackgroundTasks, limit: int | None = None, markets: str | None = None):
    """Runs in the background — check Slack for completion, or query
    contact_content_batches directly rather than trust the HTTP response."""
    market_set = set(markets.split(",")) if markets else None
    background_tasks.add_task(_submit_content_bg, limit, market_set)
    return {"status": "started"}
```

**Rule of thumb:** if an endpoint's real work involves an external API loop
over more than ~50-100 items, or polling anything that could take minutes,
wrap it in this pattern from the start rather than waiting to hit the timeout
in production.

---

## 6. Per-market-group batch selection (the actual monthly batch query)

```python
# pipelines/monthly_batch.py
MARKET_GROUPS: dict[str, set[str]] = {
    "UKI":  {"UK", "Ireland"},
    "DACH": {"DE", "AT", "CH"},
    "US":   {"US"},
    "FR":   {"FR"},
}
MARKET_TO_GROUP: dict[str, str] = {m: g for g, ms in MARKET_GROUPS.items() for m in ms}
GROUP_LIMITS: dict[str, int] = {"UKI": 500, "DACH": 500, "US": 500, "FR": 500}

async def run_monthly_batch(groups: list[str] | None = None) -> dict:
    """batch_number is scoped PER MARKET GROUP, not global — each of UKI,
    DACH, US, FR has its own independent 1, 2, 3... sequence, since they're
    pushed to Clay separately and gap-detection needs batch_number to mean
    something on its own within a group."""
    sb = get_supabase()
    active_groups = groups or list(MARKET_GROUPS.keys())
    active_markets = {m for g in active_groups for m in MARKET_GROUPS[g]}

    existing = fetch_all("campaign_batches", "domain, market, company_name, batch_number, batch_month")
    contacted = {(r["domain"], r["market"], r["company_name"]) for r in existing}

    # Next batch_number computed independently per group.
    next_batch_number_by_group = {
        g: max((r["batch_number"] for r in existing if r["market"] in MARKET_GROUPS[g]), default=0) + 1
        for g in active_groups
    }

    candidates = fetch_all(
        "priority_tam", "domain, market, company_name, ..., account_fit_score, ...",
        order_by=[("account_fit_score", True), ("prioritized_at", False)],
    )
    selected_by_group = {}
    for g in active_groups:
        limit = GROUP_LIMITS[g]
        batch_number = next_batch_number_by_group[g]
        selected_by_group[g] = [
            {**row, "batch_number": batch_number, "batch_month": date.today().replace(day=1).isoformat()}
            for row in candidates
            if row["market"] in MARKET_GROUPS[g] and (row["domain"], row["market"], row["company_name"]) not in contacted
        ][:limit]
    # ... insert selected_by_group into campaign_batches, then push each group to its own Clay webhook
```

Any function that filters `campaign_batches`/`contact_gaps`/`phantombuster_contacts`
by `batch_number` alone is a bug waiting to happen once two groups land on the
same number — always pair `batch_number` with a `market`/`market_group` filter.

---

## 7. Supabase upsert / query patterns

```python
# Single-row upsert with explicit conflict key — never a bare insert on webhook writes
sb.table("sourced_contacts").upsert(row, on_conflict="linkedin_url").execute()

# Batch upsert, chunked (Supabase/PostgREST has a practical payload size limit)
for i in range(0, len(rows), 100):
    sb.table("sourced_tam_v2").upsert(rows[i:i+100], on_conflict="domain,market,company_name").execute()

# Filtered read
sb.table("priority_tam").select("*").eq("market", "US").gte("account_fit_score", 3).execute()

# Existence check via a lookup, not a join (supabase-py has no real join support)
row = sb.table("campaign_batches").select("batch_number").eq("domain", domain).eq("market", market).limit(1).execute().data
```

---

## 8. Cache-first external API pattern

Used for the two slow/paid per-domain external calls (news search, LP
minting) — check a domain-keyed cache table first, only call out on a miss,
and only cache genuine results so transient API errors retry on the next run.

```python
# pipelines/news_search.py (pattern)
async def fetch_company_news(domain: str, company_name: str) -> dict:
    cached = sb.table("company_news_cache").select("*").eq("domain", domain).limit(1).execute().data
    if cached:
        return cached[0]
    try:
        result = await _call_claude_web_search(domain, company_name)
    except Exception:
        return _NO_NEWS  # not cached — retried next run
    sb.table("company_news_cache").upsert({"domain": domain, **result}).execute()
    return result
```

`company_lp_cache` follows the same shape (PK on `domain`), with one extra
wrinkle: it stores an `already_existed` flag from the external API, which
distinguishes "returned a fresh mint" from "returned something cached on
their side too" — useful for detecting stale/deleted pages during a
regeneration pass (compare against a fresh call and see if the flag flips).

---

## 9. Claude Batch API pattern (submit + poll)

The standard shape for anything scoring/generating many rows at once
(`enrichment.py` for account-fit/archetype, `content.py` for outbound copy):

```python
# submit: chunk rows, one Anthropic Batch job per chunk, track in a *_batches table
BATCH_SIZE = 500
for chunk in _chunks(unscored_rows, BATCH_SIZE):
    requests = [build_prompt(row) for row in chunk]
    batch = await anthropic_client.messages.batches.create(requests=requests)
    sb.table("enrichment_batches").insert({
        "batch_id": batch.id, "model": MODEL, "status": "pending",
        "companies_submitted": len(chunk), "request_mapping": {r["custom_id"]: r["domain"] for r in requests},
    }).execute()

# poll: check each pending batch_id, process results when ready
pending = sb.table("enrichment_batches").select("*").eq("status", "pending").execute().data
for batch_row in pending:
    batch = await anthropic_client.messages.batches.retrieve(batch_row["batch_id"])
    if batch.processing_status != "ended":
        continue
    async for result in anthropic_client.messages.batches.results(batch_row["batch_id"]):
        _write_back_one_result(result, batch_row["request_mapping"])
    sb.table("enrichment_batches").update({"status": "completed"}).eq("batch_id", batch_row["batch_id"]).execute()
```

The `request_mapping` jsonb column is what lets the poller map a batch
result's `custom_id` back to a `domain`/`sourced_contacts.id` without a second
round-trip — always populate it at submit time.

---

## 10. Error handling pattern

```python
import logging
logger = logging.getLogger(__name__)

# Webhook errors — raise immediately, correct status code
raise HTTPException(status_code=401, detail="invalid or missing X-Clay-Contacts-Secret")
raise HTTPException(status_code=422, detail=exc.errors())  # from a caught pydantic.ValidationError

# Pipeline errors — catch per record, log, continue; don't crash the whole batch loop
for row in rows:
    try:
        result = await call_external_api(row["domain"])
    except Exception:
        logger.exception("technographic lookup failed for %s", row["domain"])
        continue

# Background task failures — since there's no HTTP response to report through,
# self-report to Slack (see pattern #5)
except Exception as exc:
    logger.exception("content_submit: background task failed")
    await notify(f"❌ *Content generation submission failed* — `{exc}`", success=False)
```

---

## 11. Testing pattern (mocked Supabase client)

```python
# tests/test_monthly_batch.py (pattern)
from unittest.mock import MagicMock

def _chainable(rows_by_page):
    """Mocks the chained .select().eq().range().order().execute() call style,
    returning different pages via side_effect so pagination in fetch_all()
    actually terminates instead of looping forever on a naive mock."""
    mock = MagicMock()
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.order.return_value = mock
    mock.range.return_value = mock
    mock.execute.side_effect = [MagicMock(data=page) for page in rows_by_page] + [MagicMock(data=[])]
    return mock

def _patch_supabase(monkeypatch, table_data: dict[str, list[list[dict]]]):
    """Patches BOTH pipelines.monthly_batch.get_supabase and db.client.get_supabase —
    fetch_all() is imported from db.client but calls get_supabase() internally,
    so patching only the pipeline module's import misses that inner call."""
    sb = MagicMock()
    sb.table.side_effect = lambda name: _chainable(table_data.get(name, [[]]))
    monkeypatch.setattr("pipelines.monthly_batch.get_supabase", lambda: sb)
    monkeypatch.setattr("db.client.get_supabase", lambda: sb)
    return sb
```

Run: `python -m pytest -q`. As of the last full run, baseline is **16 failed /
50 passed** on this repo pre-existing state (not introduced by whatever you're
about to change) — re-verify this baseline before assuming a red test is
something you broke.

---

## 12. Cron-invoked function signature convention

Every cron target is a thin `POST` endpoint that either calls a background
function directly or schedules one via `BackgroundTasks` — cron jobs never
wait on a synchronous multi-minute response (Railway's own cron trigger has
the same edge-timeout problem as manual HTTP calls). If you add a new
recurring job, follow whichever of patterns #5 or the plain-async-call style
in `daily_runner.py` already matches its expected running time.
