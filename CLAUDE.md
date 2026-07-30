# Brevo Outbound Engine — Claude Code Context

## Project overview
A full-stack outbound GTM engine built in Python/FastAPI, deployed on Railway,
with Supabase (Postgres) as the central data warehouse. The system ingests
company TAM data from Clay, qualifies it against Brevo CRM + a technographic
API, runs an agentic domain-quality gate, scores account fit and ICP archetype
via Claude, selects monthly outbound batches per market group, sources
contacts (Clay primary, PhantomBuster fallback), generates personalised
outbound content + landing pages via Claude, and ingests engagement signals
from Lemlist and Albacross — including AI reply classification.

This file was last reconciled against the actual code, migrations, and live
Railway cron config on 2026-07-29/30. If it drifts from the code again,
trust the code — `pipelines/*.py`, `webhooks/*.py`, `supabase/migrations/*.sql`
are the ground truth, this file is a map of it.

---

## Deployment stack
- **API:** FastAPI app deployed on Railway (project `brevo_outbound_engine`,
  service `brevo_outbound_engine`), auto-deployed from this repo's `main` branch.
  Public URL: `https://brevooutboundengine-production.up.railway.app`
- **Database:** Supabase (Postgres) — existing Supabase project
- **Scheduler:** 7 Railway cron jobs (see [Cron schedule](#cron-schedule) below) —
  no external scheduler, no dbt automation
- **AI enrichment / scoring / content:** Anthropic Claude — both the Batch API
  (account fit + archetype scoring, outbound content) and direct Messages API
  with `web_search` (domain quality, news search, LinkedIn URL recovery, reply
  classification)
- **Contact sourcing fallback:** PhantomBuster (LinkedIn Company Extractor +
  Sales Navigator Search Export), for companies Clay can't source
- **Landing pages:** external Railway service (`web-production-a4433.up.railway.app`,
  owned by the project owner, not a third party) — one personalised ABM landing
  page per domain, cached in `company_lp_cache`
- **Dashboard:** Streamlit app in `dashboard/` (Streamlit Community Cloud),
  read-only against Supabase, password-gated
- **Data quality:** dbt Core project exists (`dbt/`, real models under
  `dbt/models/staging` and `dbt/models/marts`) but **is not wired into any
  cron or pipeline** — `pipelines/dbt_runner.py` exists but is dead code
  (imported by nothing). Run manually: `dbt test --profiles-dir . --target prod`.

---

## Environment variables
Confirmed against actual `os.environ[...]` / `os.getenv(...)` usage across the
codebase (`.env.example` in the repo may lag — cross-check before trusting it).

```
# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_DB_URL=

# Webhook secrets
CLAY_WEBHOOK_SECRET=                  # clay_tam.py — HMAC-SHA256, X-Clay-Signature header. FAIL-OPEN if unset (validation skipped).
CLAY_CONTACTS_WEBHOOK_SECRET=         # clay_contacts.py — static secret, X-Clay-Contacts-Secret header. FAIL-CLOSED if unset.
LEMLIST_WEBHOOK_SECRET=               # lemlist_events.py — secret is a JSON body field, not a header. FAIL-OPEN if unset. Plain != compare, not constant-time.
# albacross.py has NO auth mechanism at all — any POST is accepted. No env var gates it.

# AI
ANTHROPIC_API_KEY=

# CRM / technographics
BREVO_CRM_API_KEY=
TECHSTACK_API_KEY=
TECHSTACK_API_BASE_URL=https://techstack-api-pzd1.onrender.com

# Contact sourcing (PhantomBuster fallback)
PHANTOMBUSTER_API_KEY=
PHANTOMBUSTER_COMPANY_EXTRACTOR_ID=
PHANTOMBUSTER_SALES_NAV_ID=

# Email/gifting enrichment (one-off scripts)
APOLLO_API_KEY=
LUSHA_API_KEY=

# Landing pages
LP_GENERATOR_URL=                     # optional — defaults to https://web-production-a4433.up.railway.app/generate

# Content preview tool
CONTENT_PREVIEW_SECRET=               # gates GET/POST /tools/content-preview and /pipelines/content/preview

# Clay outbound push (monthly batch → Clay, per market group)
CLAY_WEBHOOK_UK=                      # used for both UK and Ireland (MARKET_TO_WEBHOOK_KEY)
CLAY_WEBHOOK_DACH=                    # used for DE, AT, CH
CLAY_WEBHOOK_US=                      # not in the explicit map — falls back to CLAY_WEBHOOK_{MARKET}
CLAY_WEBHOOK_FR=                      # same fallback pattern

# Ops
SLACK_WEBHOOK_URL=                    # utils/slack.py — used for daily digests, batch pushes, background-task failures
```

**Note:** `ALBACROSS_WEBHOOK_SECRET` and `LEMLIST_API_KEY` appear in the old
`.env.example` but are not referenced anywhere in current code — Albacross has
no auth at all, and nothing in this repo calls the Lemlist API directly
(Lemlist enrollment is manual CSV upload, see [Phase 4b](#phase-4b--content-generation)).

---

## Project structure
```
brevo-outbound-engine/
├── CLAUDE.md                          # this file
├── SKILL.md                           # reusable code patterns
├── api/
│   └── main.py                        # FastAPI app — registers all 13 routers
├── webhooks/                          # 4 files, all registered
│   ├── clay_tam.py                    # Clay TAM ingestion
│   ├── clay_contacts.py               # Clay contact sourcing (single-object payload)
│   ├── lemlist_events.py              # Lemlist email engagement events
│   └── albacross.py                   # Albacross website-visit signals
├── pipelines/                         # 16 files — see full inventory below
│   ├── qualification.py               # CRM check + rules + technographic
│   ├── enrichment.py                  # Claude account-fit + archetype scoring, priority_tam promotion
│   ├── domain_quality.py              # agentic bogus/subsidiary/chain-HQ gate
│   ├── monthly_batch.py               # per-market-group batch selection + Clay push
│   ├── contact_gaps.py                # PhantomBuster fallback contact sourcing
│   ├── score_contacts.py              # Claude relevance/seniority scoring of PB contacts
│   ├── linkedin_url_recovery.py       # recovers dead LinkedIn company URLs for stuck gaps
│   ├── content.py                     # outbound sequence + LP + resource generation
│   ├── lp_generator.py                # personalised landing page minting (cache-first)
│   ├── news_search.py                 # per-domain news lookup for Email 1 opener
│   ├── resource_tool.py               # static resource catalogue + shortlisting
│   ├── reply_intelligence.py          # Claude reply classification (Lemlist replies)
│   ├── crm_sync.py                    # priority_tam → Brevo CRM mass push (not API-wired)
│   ├── daily_runner.py                # 6am daily cron orchestrator
│   └── dbt_runner.py                  # DEAD CODE — imported by nothing
├── routing/                           # empty directory — router.py was never built
├── db/
│   ├── client.py                      # get_supabase() + fetch_all() pagination helper
│   └── models.py                      # Pydantic models (only 2 of 4 webhooks actually use one)
├── utils/
│   ├── linkedin.py                    # normalise_linkedin_url()
│   └── slack.py                       # notify()
├── supabase/
│   └── migrations/                    # 49 files, 001–049, run via Supabase SQL editor / CLI
├── dbt/                                # real dbt project, NOT cron-automated (see above)
│   ├── dbt_project.yml
│   └── models/{staging,marts}/
├── dashboard/                          # Streamlit app (5 pages, see below)
├── scripts/                             # 24 files — reusable ops tools + one-off import/enrichment scripts
├── tests/                              # 5 files, pytest
└── data/                                # CSV exports, one-off import sources, scratch outputs
```

---

## Database schema
49 migrations (`001_sourced_tam.sql` … `049_campaign_batches_full_priority_tam_parity.sql`).
**Important:** the migration folder is not a complete picture of the live
schema — several things exist out-of-band (applied directly in Supabase, no
migration file):

| Out-of-band item | Detail |
|---|---|
| `sourced_tam_v2` | Migration 001 creates a table literally named `sourced_tam`. Every later migration and all pipeline code reference `sourced_tam_v2`. The rename happened directly in Supabase — no `ALTER TABLE ... RENAME` exists in `supabase/migrations/`. |
| `pipeline_locks` | Used in `pipelines/qualification.py` as a mutex around the technographic step (`insert`/`delete` on `name='technographic'`). No `CREATE TABLE` anywhere. |
| `priority_tam` extra columns | `business_model`, `company_revenue`, `multi_entity`, `tam_segment`, `icp_archetype_primary/secondary/evidence` exist on `priority_tam` with no migration adding them (migration 049's comment acknowledges this — it only backfills the same columns onto `campaign_batches` for parity). |
| `touchpoints` | **Never existed as a table.** Only appears as prose inside Claude content-generation prompts. Purely vestigial — if you see it in an old doc, ignore it. |

### Core tables (current effective schema, drops/renames folded in)

| Table | Purpose | Written by | Read by |
|---|---|---|---|
| `sourced_tam_v2` (~68k rows) | Raw TAM from Clay, one row per company per market | `webhooks/clay_tam.py` (upsert) | `qualification.py` (CRM check) |
| `qualified_tam_v2` (~67k rows) | Post-CRM, post-rules, post-technographic, post-domain-quality, post-AI-fit-score companies. The most-referenced table in the codebase. | `qualification.py`, `domain_quality.py`, `enrichment.py` | almost everything upstream of batch selection |
| `priority_tam` (~34k rows) | `account_fit_score >= 3` companies eligible for monthly batch selection, gated by domain-quality status | `enrichment.py::run_prioritize` (excludes `brevo_company_id` deliberately — see [Known issues](#known-issues--stale-flags)) | `monthly_batch.py`, `crm_sync.py` |
| `priority_tam_parked` | Side-table of excluded shared-domain / chain-brand rows (created via `CREATE TABLE ... LIKE priority_tam`, migration 044) | manual/SQL only | `domain_quality.py` (`--parked-only` mode) |
| `campaign_batches` (~2.7k rows) | Audit log of every company ever selected into a batch. `batch_number` is scoped **per market group**, not global (see [Phase 4a](#phase-4a--monthly-batch-selection)) | `monthly_batch.py` | `clay_contacts.py` (batch_number resolution), `contact_gaps.py`, `dashboard` |
| `sourced_contacts` (~4.3k rows) | Contacts sourced for batch companies, from Clay or promoted PhantomBuster scrapes. Unique key is `linkedin_url` (not `domain+email` — swapped in migration 037 because emailless contacts collided on NULL). | `clay_contacts.py`, `score_contacts.py` | `content.py`, `export_lemlist_csv.py` |
| `contact_gaps` | PhantomBuster fallback state machine for batch companies Clay didn't source | `contact_gaps.py` | `contact_gaps.py`, `linkedin_url_recovery.py` |
| `contact_gaps_failed` | Dead-letter archive for permanently-unrecoverable gap rows | `contact_gaps.py` | dashboard only |
| `phantombuster_contacts` | Raw PB scrape landing table, scored then promoted top-N/domain into `sourced_contacts` | `contact_gaps.py` (write), `score_contacts.py` (score+promote) | `score_contacts.py` |
| `contact_content_batches` | Tracks Anthropic Batch API jobs for outbound content | `content.py` | `content.py` (poller) |
| `enrichment_batches` | Tracks Anthropic Batch API jobs for account-fit/archetype scoring | `enrichment.py` | `enrichment.py` (poller) |
| `company_lp_cache` | One row per domain — cached landing page URL, PK on `domain` | `lp_generator.py` | `content.py`, dashboard |
| `company_news_cache` | One row per domain — cached news-search result, PK on `domain` | `news_search.py` | `content.py` |
| `reply_classifications` | Claude verdicts on Lemlist replies, idempotent on `lemlist_activity_id` (partial unique index) | `webhooks/lemlist_events.py` (background task), `reply_intelligence.py` | reply-intelligence, dashboard |
| `lemlist_activities` | Org-wide Lemlist event firehose, plain insert per event (no dedup key) | `webhooks/lemlist_events.py` | dashboard, `reply_intelligence.py` |
| `albacross_signals` | Website-visit signals, plain insert | `webhooks/albacross.py` (background task) | dashboard |
| `pipeline_locks` | Out-of-band mutex table (see above) | `qualification.py` | `qualification.py` |

### Tables that exist in migrations but nothing in the codebase reads/writes
`hot_signals`, `lead_routing`, `blacklist`, `requeue_timing`, `bounce_analysis` —
all have real `CREATE TABLE` migrations (022, 023, 025, 027, 028) but zero
`.table()` references anywhere in Python. Likely planned-feature or
dashboard/manual tables; don't assume anything actively writes them.

---

## API endpoints
All routers are registered in `api/main.py`. 13 routers + inline `/health`.

### Webhooks (inbound, data ingestion)
| Method | Endpoint | Auth | Writes to |
|---|---|---|---|
| POST | `/webhooks/clay/tam` | HMAC-SHA256 (`X-Clay-Signature`), **fail-open** if secret unset | `sourced_tam_v2` |
| POST | `/webhooks/clay/contacts` | Static secret (`X-Clay-Contacts-Secret`), **fail-closed** | `sourced_contacts` |
| POST | `/webhooks/lemlist` | Secret in JSON body, **fail-open** if unset, plain `!=` compare | `lemlist_activities` (+ `reply_classifications` for ABM-v2 replies only) |
| POST | `/webhooks/albacross` | **None** | `albacross_signals` |

### Pipeline endpoints (manual or cron-invoked — see [cron schedule](#cron-schedule) for which)
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/pipelines/run-daily` | Daily orchestrator: CRM check → rules → technographic → (enrich + content + prioritize, unless technographic lock skipped) → health snapshot → on day 1, monthly batch |
| POST | `/pipelines/qualify` | CRM check + rules + technographic in one call |
| POST | `/pipelines/crm-check` | CRM check only |
| POST | `/pipelines/enrich` | Submit account-fit/archetype Claude batch |
| POST | `/pipelines/enrich/complete` | Process one batch_id |
| POST | `/pipelines/enrich-complete-all` | Poll all pending enrichment batches |
| POST | `/pipelines/prioritize` | Promote fit≥3 rows to `priority_tam` |
| POST | `/pipelines/domain-quality` | Run the agentic domain-quality gate (`limit`, `target_ids`) |
| POST | `/pipelines/monthly-batch` | Select next batch (`?groups=DACH,US` subset) |
| POST | `/pipelines/monthly-batch/push` | Push one group's batch to Clay (`market_group` + `batch_number` both required) |
| POST | `/pipelines/run-monthly` | Select + push, all groups, background |
| POST | `/pipelines/contact-gaps` | Detect gaps + launch PB phase 1 for one `market_group`+`batch_number` |
| GET | `/pipelines/contact-gaps/sales-nav-csv` | Unauth CSV feed for PhantomBuster to fetch |
| POST | `/pipelines/contact-gaps/run-latest` | Loop all groups, latest batch each |
| POST | `/pipelines/contact-gaps/digest` | Slack progress digest |
| POST | `/pipelines/contact-gaps/poll` | 5 internal burst cycles (~1 min cadence) |
| POST | `/pipelines/diagnose/pb-extract` | Single-URL PB trace, debugging |
| POST | `/pipelines/score-contacts` | Claude relevance/seniority scoring of PB contacts |
| GET | `/pipelines/score-contacts/preview` | Read-only ranked candidates |
| POST | `/pipelines/score-contacts/promote` | Promote top-N/domain into `sourced_contacts` |
| POST | `/pipelines/recover-linkedin-urls` | Claude+web_search recovery for dead PB LinkedIn URLs |
| POST | `/pipelines/content/preview` | Preview one contact's generated content (needs `X-Preview-Secret`) |
| GET | `/tools/content-preview` | Static HTML preview tool |
| POST | `/pipelines/content/submit` | Submit outbound content batch (`?markets=` subset override), **BackgroundTasks** |
| POST | `/pipelines/content-complete-all` | Poll all pending content batches, **BackgroundTasks** |
| GET | `/health` | liveness |

Not API-wired at all (library imports or run via `scripts/` only): `crm_sync.py`,
`dbt_runner.py` (dead), `reply_intelligence.py`, `news_search.py`,
`lp_generator.py`, `resource_tool.py`.

---

## Cron schedule
7 Railway cron jobs, confirmed live via `railway status` (project `brevo_outbound_engine`).

| Cron job | Schedule (UTC) | Target endpoint |
|---|---|---|
| daily-pipeline | `0 0 * * *` | `/pipelines/run-daily` |
| enrich-poller | `*/30 * * * *` | `/pipelines/enrich-complete-all` then `/pipelines/content-complete-all` |
| score-contacts-cron | `0 0 * * *` | `/pipelines/score-contacts` |
| contact-gaps-digest | `0 7 * * *` | `/pipelines/contact-gaps/digest` |
| monthly-batch | `0 9 1 * *` | `/pipelines/run-monthly` (**not** `/pipelines/monthly-batch` — different endpoint) |
| trigger-contact-gaps | `0 0 2 * *` | `/pipelines/contact-gaps/run-latest` |
| contact-gaps-poll | `*/5 * * * *` | `/pipelines/contact-gaps/poll` |

`/pipelines/monthly-batch`, `/pipelines/recover-linkedin-urls`, `/pipelines/domain-quality`,
and all `/pipelines/qualify`, `/pipelines/enrich`, `/pipelines/content/submit` variants
are **manual-only** — nothing crons them directly (daily-pipeline calls the
underlying functions in-process, not via HTTP).

---

## Pipeline flow (end to end)

### Phase 1 — TAM sourcing
Clay table run (one per market) → `POST /webhooks/clay/tam` → HMAC validated →
upsert into `sourced_tam_v2` on `(domain, market, company_name)`. `market` is
derived from the payload's `Country` field via a 16-entry lookup, not sent directly.

### Phase 2 — CRM check + rules + technographic (daily cron)
`run_crm_check()` → Brevo CRM lookup, writes `crm_checked=true` + deal/company
fields → `run_qualification_rules()` → drops existing customers / active deals,
upserts survivors into `qualified_tam_v2` → `run_technographic()` → calls the
Technostack API (30 req/min hard cap, currently serialized at concurrency 1 —
see [Known issues](#known-issues--stale-flags)), writes `tech_*` columns +
derives `esp_detected`/`esp_score` from `tech_esp` via a competitor-ESP scoring
rubric (Mailchimp-tier ESPs score highest, Salesforce/Marketo lowest).
Guarded by the `pipeline_locks` mutex — if technographic is already running,
that day's enrich/content/prioritize steps are skipped entirely (not queued).

### Phase 3 — Domain quality gate
Runs independently (manual trigger, `/pipelines/domain-quality`) over
`qualified_tam_v2` rows with `domain_quality_checked_at IS NULL`. A Claude
Haiku agent with 3 tools (bogus-pattern regex, shared-domain lookup, verdict
save) classifies each domain as `verified/bogus/subsidiary/corrected` and a
role (`regional_hq/country_hq/global_hq/property/branch/franchisee/independent`).
This verdict gates promotion into `priority_tam` — blocked statuses are
`subsidiary`/`bogus`, blocked roles are `property`/`branch`/`franchisee`.

### Phase 4 — AI enrichment (account fit + ICP archetype)
`submit_enrichment()` chunks unscored `qualified_tam_v2` rows into batches of
500, submits to Claude Batch API (with `web_search`), gets back
`account_fit_score` (1-5), `vertical`, `account_narrative`, and one of 6 ICP
archetypes (**Graduate, Network, Consolidator, Email Specialist, Feature
Specialist, Saver**) + evidence. The `enrich-poller` cron (every 30 min)
processes completed batches. `run_prioritize()` then promotes fit≥3 rows
(passing the domain-quality gate) into `priority_tam` — deliberately
**excluding `brevo_company_id`** from the upsert (a prior incident created ~6k
duplicate Brevo CRM records when this wasn't excluded).

### Phase 4a — Monthly batch selection
1st-of-month cron (`/pipelines/run-monthly`). Selects the next never-contacted
companies from `priority_tam` per **market group** — `MARKET_GROUPS = {"UKI":
{"UK","Ireland"}, "DACH": {"DE","AT","CH"}, "US": {"US"}, "FR": {"FR"}}`, each
capped at 500. **`batch_number` is scoped per group, not global** — UKI, DACH,
US, and FR each have their own independent 1, 2, 3... sequence, because they're
pushed to Clay separately and gap-detection needs to know which group's "batch
1" it's looking at. Selected rows insert into `campaign_batches`, then each
group's batch is pushed to its own Clay webhook (`CLAY_WEBHOOK_UK` for
UK+Ireland, `CLAY_WEBHOOK_DACH` for DE/AT/CH, `CLAY_WEBHOOK_US`/`CLAY_WEBHOOK_FR`
by convention fallback).

Clay sources contacts and calls back `POST /webhooks/clay/contacts` (one
contact per call, static-secret auth) → upsert into `sourced_contacts` on
`linkedin_url`. For companies Clay can't source, the **contact-gaps** pipeline
takes over: Phase 1 (LinkedIn Company Extractor → org id → Sales Nav URL),
Phase 2 (Sales Nav Search Export scrape → `phantombuster_contacts`), scored by
Claude (`score_contacts.py`, relevance≥3 required) and top-10/domain promoted
into `sourced_contacts` — never overwriting existing Clay-sourced rows.
Dead/unrecoverable LinkedIn URLs get one more shot via
`linkedin_url_recovery.py` (Claude + web_search) before archiving to
`contact_gaps_failed`.

### Phase 4b — Content generation
`submit_content()` is scoped to `CONTENT_GENERATION_MARKETS` in
`pipelines/content.py` (currently `{"DE","AT","CH","US"}` at the code level —
**but DACH is operationally paused per an explicit decision, do not submit
DACH content without checking current status first**; FR was added via the
`markets=` override param and is fully live end-to-end as of 2026-07-28). For
each pending contact: fetches company news (Claude + web_search, cached per
domain), mints/reuses a personalised landing page (external LP service,
cached per domain, `create_abm1` payload with market as uppercase
`UKI|DACH|USA|FR` and archetype as a snake_case slug), shortlists relevant
resources (`resource_tool.py`, 241-entry static catalogue), and generates the
outbound sequence via Claude Batch API using a market-localised prompt
template (EN / DE / FR). Runs as a `BackgroundTasks` job — both
`/pipelines/content/submit` and `/pipelines/content-complete-all` were
converted to this pattern after synchronous execution exceeded Railway's edge
timeout on multi-minute runs (see [SKILL.md](SKILL.md)).

Contacts with generated content are exported via
`scripts/export_lemlist_csv.py --market-group <group> --batch-number <n>` and
uploaded to Lemlist manually by a BDR — there is no programmatic Lemlist push.

### Phase 5 — Engagement signals
Lemlist (`POST /webhooks/lemlist`) and Albacross (`POST /webhooks/albacross`)
both write to their own tables in real time. Lemlist replies for one specific
campaign (`cam_cjkdYRBDEZFaXXYxo`, the UKI ABM v2 campaign — hardcoded, not
yet generalised) are classified by Claude into 10 buckets and Slack-notified;
all other campaigns' replies land in `lemlist_activities` unclassified unless
`scripts/run_reply_classifier.py` is run manually.

### CRM sync (separate, not cron-automated)
`scripts/run_crm_sync.py` (wraps `pipelines/crm_sync.py`) pushes `priority_tam`
→ Brevo CRM Company records, PATCH if `brevo_company_id` exists else POST with
a self-heal website lookup to avoid duplicates. Run manually, not on a cron.

---

## Coding conventions
- Python 3.11+, FastAPI, Pydantic v2
- **DB access:** `db.client.get_supabase()` for a raw client, `db.client.fetch_all(table, select, filters, limit, order_by)` for paginated reads — it always appends an `id` tiebreaker to `order_by` because PostgREST doesn't guarantee stable ordering across paginated `.range()` calls without one
- **Upserts, not inserts**, on all webhook writes, with an explicit `on_conflict` key — this project has hit real dedup-key bugs before (`sourced_contacts` swapped its unique key from `(domain,email)` to `linkedin_url` in migration 037 specifically because NULL emails were colliding)
- **Webhook auth is inconsistent by design** — check the actual validation function before assuming a mechanism; two webhooks fail-open if their secret env var is unset (`clay_tam`, `lemlist_events`), one is fail-closed (`clay_contacts`), one has no auth at all (`albacross`)
- **Long-running endpoints use `BackgroundTasks`**, not inline execution — Railway's edge proxy times out well before a multi-minute batch operation finishes; the pattern is: endpoint schedules an internal `_..._bg()` async function via `background_tasks.add_task(...)`, returns `{"status":"started"}` immediately, and the bg function self-reports success/failure via `utils.slack.notify()`
- **Cache-first external API calls** — `lp_generator.py` and `news_search.py` both check a domain-keyed cache table before calling their (slow/paid) external API, and only cache genuine results (API errors are not cached, so they retry next run)
- Claude Batch API is used for anything scoring/generating many rows at once (account fit, archetype, outbound content); direct Messages API + `web_search` is used for one-off agentic tasks (domain quality, news search, LinkedIn recovery, reply classification)
- Pipeline errors are caught per-record and logged, not allowed to crash the whole batch loop
- All webhook/pipeline endpoints return `{"status": "ok", ...}` on success; errors return `{"status": "error", "detail": "..."}` with the correct HTTP status

---

## Known issues / stale flags
Worth checking before relying on these:

- `pipelines/qualification.py`: `_TECH_CONCURRENCY = 1` is a "temporarily lowered for testing" value that was never reverted — comment says to revert to 6 once confirmed stable.
- `pipelines/contact_gaps.py`: `PHASE2_BATCH_SIZE = 5` is declared but not honoured — PhantomBuster doesn't accept multi-line input for this launcher, so it processes 1 URL/launch regardless.
- `pipelines/contact_gaps.py`'s `_REGION` map and `pipelines/monthly_batch.py`'s `MARKET_TO_WEBHOOK_KEY` both have **no US or FR entries** — US/FR fall back to defaults (region falls back to the UK Sales Nav region id, which is a latent bug for FR/US contact-gap scraping specifically; webhook key falls back to `CLAY_WEBHOOK_{MARKET}` by naming convention, which is fine).
- `pipelines/dbt_runner.py` is dead code — imported by nothing, despite `/pipelines/enrich-complete-all`'s docstring still claiming dbt runs after completion.
- `pipelines/reply_intelligence.py` is hardcoded to a single campaign id (`cam_cjkdYRBDEZFaXXYxo`) and has a dead `if False` branch (harmless, never executes).
- `routing/` is an empty directory — a `router.py` for rep round-robin + Lemlist enrollment was planned but never built; there is no programmatic routing anywhere in this codebase (Lemlist upload is manual CSV).
- `scripts/archive/run_test_batch.py` imports `select_resource` from `pipelines/resource_tool.py`, which no longer exists there (only `get_all_resources`/`shortlist_resources` remain) — this script is broken/dead.
- No French Tone-of-Voice reference deck exists (unlike German, which has one) — the FR content prompt template defaults to formal `vous` and a judgment-call jargon list; flag if Brevo produces a real FR ToV deck.
- Test coverage gaps: no test file exists for `webhooks/lemlist_events.py`, `webhooks/albacross.py`, or pipelines `daily_runner`, `content`, `contact_gaps`, `score_contacts`, `domain_quality`, `linkedin_url_recovery`, `crm_sync` — notably several **cron-invoked** pipelines have zero test coverage.

---

## Open items
1. `CONTENT_GENERATION_MARKETS` in `pipelines/content.py` still includes DE/AT/CH at the code level even though DACH is operationally paused — don't submit DACH content without confirming current status, since the code alone won't stop you.
2. FR/US region fallback bug in `contact_gaps.py::_build_sales_nav_url` (see Known issues above) — not yet fixed.
3. `_TECH_CONCURRENCY` needs reverting from 1 to 6 once stability is reconfirmed.
4. dbt is not automated on any cron — tests must be run manually; consider whether that's intentional or a gap.
5. No FR Tone-of-Voice deck — current FR prompt template is a judgment call, not confirmed brand guidance.
