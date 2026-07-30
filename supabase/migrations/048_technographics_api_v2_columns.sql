-- New Technographics API (techstack-api-pzd1.onrender.com) replaces the old
-- Cloudflare-gated internal endpoint. Adds the richer category-list columns
-- alongside the existing esp_detected/esp_score, which are now DERIVED from
-- tech_esp rather than computed directly from the API response.
--
-- esp_detected/esp_score are kept as-is (read downstream by crm_sync.py and
-- monthly_batch.py) — no consumer of those columns needs to change.

ALTER TABLE qualified_tam_v2
    ADD COLUMN IF NOT EXISTS tech_score          int,
    ADD COLUMN IF NOT EXISTS tech_stack_primary   text,
    ADD COLUMN IF NOT EXISTS tech_category        text,
    ADD COLUMN IF NOT EXISTS tech_esp             text,
    ADD COLUMN IF NOT EXISTS tech_crm             text,
    ADD COLUMN IF NOT EXISTS tech_cms             text,
    ADD COLUMN IF NOT EXISTS tech_ecommerce       text,
    ADD COLUMN IF NOT EXISTS tech_analytics       text,
    ADD COLUMN IF NOT EXISTS tech_cdn             text,
    ADD COLUMN IF NOT EXISTS tech_payment         text,
    ADD COLUMN IF NOT EXISTS tech_marketing       text,
    ADD COLUMN IF NOT EXISTS tech_chat            text,
    ADD COLUMN IF NOT EXISTS tech_hosting         text,
    ADD COLUMN IF NOT EXISTS tech_ab_testing      text,
    ADD COLUMN IF NOT EXISTS tech_tag_manager     text,
    ADD COLUMN IF NOT EXISTS tech_checked_at      timestamptz;

ALTER TABLE priority_tam
    ADD COLUMN IF NOT EXISTS tech_score          int,
    ADD COLUMN IF NOT EXISTS tech_stack_primary   text,
    ADD COLUMN IF NOT EXISTS tech_category        text,
    ADD COLUMN IF NOT EXISTS tech_esp             text,
    ADD COLUMN IF NOT EXISTS tech_crm             text,
    ADD COLUMN IF NOT EXISTS tech_cms             text,
    ADD COLUMN IF NOT EXISTS tech_ecommerce       text,
    ADD COLUMN IF NOT EXISTS tech_analytics       text,
    ADD COLUMN IF NOT EXISTS tech_cdn             text,
    ADD COLUMN IF NOT EXISTS tech_payment         text,
    ADD COLUMN IF NOT EXISTS tech_marketing       text,
    ADD COLUMN IF NOT EXISTS tech_chat            text,
    ADD COLUMN IF NOT EXISTS tech_hosting         text,
    ADD COLUMN IF NOT EXISTS tech_ab_testing      text,
    ADD COLUMN IF NOT EXISTS tech_tag_manager     text;
