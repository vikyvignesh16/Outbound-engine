-- Cache for personalised ABM landing pages minted by the external page
-- generator at https://web-production-a4433.up.railway.app/generate.
--
-- The API takes 35-45s per call and is idempotent per company (same company
-- returns the existing page). We mint once per domain ever and reuse the URL
-- across every contact at that company and every subsequent batch — manual
-- DELETE on company_lp_cache to refresh.
--
-- Failures (network, 422, 502) deliberately don't write a row so the next
-- batch can retry. A successful mint with already_existed=true is still a
-- valid cache fill — the upstream API gave us a real URL we can serve.

CREATE TABLE IF NOT EXISTS company_lp_cache (
    domain           text PRIMARY KEY,
    preview_url      text NOT NULL,
    slug             text,
    market           text,
    already_existed  boolean,
    raw              jsonb,
    cached_at        timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS company_lp_cache_cached_at_idx
    ON company_lp_cache (cached_at);

GRANT ALL ON public.company_lp_cache TO anon, authenticated, service_role, postgres;
