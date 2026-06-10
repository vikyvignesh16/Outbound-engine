-- Cache for the per-domain news search step that feeds Email 1's "I came across..."
-- opener in the content generation pipeline (see pipelines/news_search.py).
--
-- The search is paid (Anthropic web_search tool, ~$0.01 per call) and the result
-- doesn't change daily for most companies, so we cache one row per domain.
--
-- Lookup is cache-first: pipelines/news_search.fetch_company_news() returns the
-- cached row if any, otherwise calls Anthropic Messages with the web_search tool,
-- writes the result, and returns it. No automatic invalidation — to refresh a
-- domain's news, delete the row manually:
--   DELETE FROM company_news_cache WHERE domain = 'foo.com';
--
-- Failed searches (API errors) deliberately don't write a row, so the next batch
-- will retry. Rows with found=false / usable=false ARE persisted — that's a
-- valid "we looked, nothing usable" answer that shouldn't be re-paid for.

CREATE TABLE IF NOT EXISTS company_news_cache (
    domain        text PRIMARY KEY,
    found         boolean NOT NULL,
    usable        boolean NOT NULL,
    news_summary  text,
    news_type     text,
    raw           jsonb,
    cached_at     timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS company_news_cache_cached_at_idx
    ON company_news_cache (cached_at);

-- Supabase doesn't auto-grant role access to tables created via the MCP
-- apply_migration path; mirror the standard grants the SQL editor would
-- apply by default so the service_role used by db.client can read/write.
GRANT ALL ON public.company_news_cache TO anon, authenticated, service_role, postgres;
