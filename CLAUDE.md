# Brevo Outbound Engine — Claude Code Context

## Project overview
A full-stack outbound GTM engine for Brevo built in Python/FastAPI,
deployed on Railway, with Supabase (Postgres) as the central data
warehouse. The system ingests company TAM data from Clay, qualifies
and enriches it, monitors engagement touchpoints from Albacross and
Lemlist, and automates contact sourcing and routing into Lemlist
sequences and Brevo CRM.

## Deployment stack
- **API:** FastAPI app deployed on Railway (existing Railway project)
- **Database:** Supabase (Postgres) — existing Supabase project
- **Scheduler:** Railway cron job — triggers monthly batch pipeline on 1st of month
- **AI enrichment:** Claude Batch API (Anthropic)
- **Data quality:** dbt Core (open source, free, triggered via Railway cron)

---

## Environment variables
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_DB_URL=                  # direct Postgres connection string for asyncpg
CLAY_WEBHOOK_SECRET=              # ⚠️ PENDING: confirm with Clay
ALBACROSS_WEBHOOK_SECRET=         # ⚠️ PENDING: confirm with Albacross
LEMLIST_WEBHOOK_SECRET=           # ⚠️ PENDING: confirm with Lemlist
ANTHROPIC_API_KEY=
BREVO_CRM_API_KEY=
TECHNOGRAPHIC_API_KEY=            # ⚠️ PENDING: confirm internal API
LEMLIST_API_KEY=
```

---

## Project structure
```
brevo-outbound-engine/
├── CLAUDE.md                          # this file — read at start of every session
├── SKILL.md                           # reusable code patterns for this project
├── api/
│   └── main.py                        # FastAPI app — registers all routers
├── webhooks/
│   ├── clay_tam.py                    # Step 1  — TAM ingestion from Clay
│   ├── albacross.py                   # Step 7  — Albacross visit events
│   ├── albacross_transformer.py       # Step 7  — formats raw Albacross → clean jsonb
│   ├── lemlist.py                     # Step 7  — Lemlist email events
│   └── clay_contacts.py              # Step 10 — contacts sourced from Clay
├── pipelines/
│   ├── qualification.py               # Steps 2-4 — technographic + CRM + rules
│   ├── enrichment.py                  # Step 5  — Claude Batch API ICP scoring
│   └── monthly_batch.py              # Step 9  — select next 1000 companies
├── routing/
│   └── router.py                      # Step 11 — rep assignment + Lemlist + CRM
├── db/
│   ├── client.py                      # Supabase client + asyncpg connection
│   └── models.py                      # Pydantic models for all payloads
├── supabase/
│   └── migrations/
│       ├── 001_sourced_tam.sql        # run first
│       ├── 002_touchpoints.sql        # run second
│       ├── 003_contacts_sourced.sql   # run third
│       ├── 004_campaign_batches.sql   # run fourth
│       └── 005_contacts_routed.sql   # run fifth
├── dbt/
│   └── models/
│       └── tests/
└── tests/
    ├── test_clay_tam.py
    ├── test_albacross.py
    ├── test_lemlist.py
    └── test_clay_contacts.py
```

---

## Database tables
All migrations live in supabase/migrations/ and must be run in order.
Apply via Supabase SQL editor or Supabase CLI: `supabase db push`

### sourced_tam (migration 001)
Primary table for all TAM companies sourced from Clay.
Enriched in-place by the qualification and AI enrichment pipelines.
One row per company per market. Upsert on (domain, market).

### touchpoints (migration 002)
Unified engagement signal table for all sources.
Albacross (website visits) and Lemlist (email events) both write here.
Shared columns capture what every event has in common.
Source-specific data lives in payload jsonb.

**Albacross payload jsonb structure:**
```json
{
  "visit": {
    "page_url": "/pricing",
    "duration_seconds": 142,
    "pages_viewed": 4,
    "referrer": "google"
  },
  "firmographics": {
    "industry": "SaaS",
    "employee_range": "50-200",
    "country": "FR",
    "revenue_range": "1M-10M"
  },
  "session": {
    "first_visit": false,
    "visit_count": 3,
    "last_seen": "2026-05-01T14:32:00Z"
  }
}
```

**Lemlist payload jsonb structure:**
```json
{
  "campaign": {
    "id": "camp_abc123",
    "name": "FR SaaS Q2 Outbound",
    "step": 2
  },
  "engagement": {
    "event_type": "email_click",
    "clicked_url": "https://brevo.com/features",
    "device": "desktop"
  },
  "lead": {
    "lemlist_id": "lead_xyz",
    "first_name": "Jean",
    "last_name": "Dupont"
  }
}
```

### contacts_sourced (migration 003)
All contacts sourced by Clay/Claygent per company.
Written to by /webhooks/clay/contacts.
Status updated by routing pipeline.

### campaign_batches (migration 004)
Audit log of every company selected in a monthly batch run.
Used to track which companies have been contacted and ensure
sequential non-repeating selection. Each domain appears once ever.

### contacts_routed (migration 005)
Append-only log of every contact routing action.
Never update rows — each routing event is a new row.

---

## API endpoints

### Webhook endpoints (data ingestion)
| Method | Endpoint | Source | Writes to |
|---|---|---|---|
| POST | /webhooks/clay/tam | Clay TAM tables (per market) | sourced_tam |
| POST | /webhooks/albacross | Albacross | touchpoints |
| POST | /webhooks/lemlist | Lemlist | touchpoints |
| POST | /webhooks/clay/contacts | Clay contact sourcing | contacts_sourced |

### Pipeline endpoints (data processing)
| Method | Endpoint | Does | Reads | Writes |
|---|---|---|---|---|
| POST | /pipelines/qualify | Technographic + CRM + rules | sourced_tam | sourced_tam |
| POST | /pipelines/enrich | Claude Batch API ICP scoring | sourced_tam | sourced_tam |
| POST | /pipelines/monthly-batch | Select next 1000 companies | sourced_tam, campaign_batches | campaign_batches |
| POST | /pipelines/route | Rep assignment + enrollment | contacts_sourced | contacts_routed |

---

## The 12-step process

### Step 1 — TAM sourcing
**File:** `webhooks/clay_tam.py`
**Trigger:** Clay webhook fires when a Clay table run completes (one table per market)
**Flow:** POST /webhooks/clay/tam → validate Clay signature → parse payload →
normalise to consistent schema → upsert sourced_tam on (domain, market)
⚠️ PENDING: Sample Clay webhook payload + confirmation of how market is identified

### Step 2 — Technographic qualification
**File:** `pipelines/qualification.py`
**Trigger:** Called after Step 1 or manually via POST /pipelines/qualify
**Flow:** Read unqualified rows from sourced_tam → call Technographic API per domain
→ returns esp_detected + esp_score → update sourced_tam
⚠️ PENDING: Technographic API endpoint, auth method, and response schema

### Step 3 — CRM enrichment
**File:** `pipelines/qualification.py` (same pipeline as Step 2)
**Flow:** For each company passing esp_score threshold → call Brevo CRM API →
returns brevo_company_id, open_deals, planhat_id, deal_lost_date → update sourced_tam
⚠️ PENDING: Brevo CRM API endpoint and auth confirmed

### Step 4 — Rule-based qualification filter
**File:** `pipelines/qualification.py` (rules engine within same pipeline)
**Flow:** Evaluate esp_score + CRM fields against defined rules →
set qualified = true/false + disqualification_reason → update sourced_tam
⚠️ PENDING: Exact qualification rules to be defined

### Step 5 — AI enrichment (Claude Batch API)
**File:** `pipelines/enrichment.py`
**Flow:** Read qualified companies from sourced_tam → bundle into Claude Batch API job
→ each company gets structured prompt with domain, vertical, technographic data →
Claude returns account_fit_score (1-5), vertical, account_narrative →
upsert back to sourced_tam
**Important:** Batch API is async — poll for completion, write results when ready

### Step 6 — Sourced TAM complete
sourced_tam is now fully enriched. Companies with account_fit_score >= 3
are eligible for monthly batch selection.

### Step 7 — Touchpoint ingestion
**Files:** `webhooks/albacross.py`, `webhooks/albacross_transformer.py`, `webhooks/lemlist.py`
**Trigger:** Real-time webhooks from Albacross and Lemlist
**Albacross flow:** POST /webhooks/albacross → validate signature → pass raw payload
to albacross_transformer.py → build clean payload jsonb → write to touchpoints
**Lemlist flow:** POST /webhooks/lemlist → validate signature → normalise to clean
payload jsonb → extract domain from email → write to touchpoints
⚠️ PENDING: Sample Albacross payload + sample Lemlist payload (field names)

### Step 8 — Intent scoring
**Location:** Supabase materialized view `domain_abm_engagement_scores`
**Trigger:** Refreshed daily via pg_cron
**Weighting:** Albacross 40% / Lemlist 35% / LinkedIn Ads 25%
**Output:** Score tier per domain: cold / warming / hot / ready

### Step 9 — Monthly batch selection
**File:** `pipelines/monthly_batch.py`
**Trigger:** Railway cron job — runs 1st of every month
**Selection query:**
```sql
SELECT domain, market, company_name, account_fit_score, vertical
FROM sourced_tam
WHERE account_fit_score >= 3
AND domain NOT IN (SELECT domain FROM campaign_batches)
ORDER BY account_fit_score DESC, created_at ASC
LIMIT 1000;
```
**Important:** Sequential — no time window exclusion. Each monthly run picks up
the next 1000 never-contacted companies working through the full qualified TAM.

### Step 10 — Contact sourcing
**File:** `webhooks/clay_contacts.py`
**Trigger:** Clay webhooks back after sourcing contacts for selected domains
**Flow:** POST /webhooks/clay/contacts → validate signature → parse contacts →
write to contacts_sourced with status = 'new'
⚠️ PENDING: Clay contacts webhook payload schema

### Step 11 — Contact routing
**File:** `routing/router.py`
**Flow:** Read contacts_sourced WHERE status = 'new' → round-robin rep assignment
→ enroll in correct Lemlist sequence for market + vertical combination →
create deal in Brevo CRM → write to contacts_routed →
update contacts_sourced status = 'enrolled'
⚠️ PENDING: Rep list + Lemlist campaign IDs per market and vertical

### Step 12 — dbt tests
**Location:** `dbt/models/tests/`
**Trigger:** Run via dbt Core after each major pipeline write
**Command:** `dbt test --profiles-dir . --target prod`
**Tests cover:** Schema integrity, referential integrity, business logic assertions

---

## Coding conventions
- Python 3.11+
- FastAPI for all API endpoints
- Pydantic v2 for all request/response models
- `supabase-py` for simple single-table reads/writes
- `asyncpg` for complex joins and multi-table operations
- All endpoints return `{"status": "ok", "inserted": n}` on success
- All errors return `{"status": "error", "detail": "..."}` with correct HTTP status
- Webhook endpoints always validate signatures before any processing
- Always store raw payload in jsonb `raw` column before transformation
- Use upsert (not insert) on all webhook write operations to handle re-runs safely
- Never update rows in contacts_routed — append only

---

## Open items — do not build steps that depend on these until confirmed
1. Clay TAM webhook payload — exact field names
2. Clay market field — is market in the payload or identified by which Clay table fires?
3. Albacross webhook payload — exact field names and structure
4. Lemlist webhook payload — exact field names per event type
5. Clay contacts webhook payload — exact field names
6. Technographic API — endpoint, auth, response schema
7. Qualification rules — exact logic to be defined
8. Rep list — rep IDs for round-robin assignment
9. Lemlist campaign IDs — one per market + vertical combination
