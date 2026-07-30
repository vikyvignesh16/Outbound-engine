-- campaign_batches was missing several columns that priority_tam has gained
-- over time (archetype, tam_segment, business_model, company_revenue,
-- multi_entity, and the full tech_* set) — the monthly batch selection and
-- Clay push queries never selected them, so they silently never reached
-- Clay. Bringing campaign_batches to full column parity with priority_tam
-- so the pipeline queries (pipelines/monthly_batch.py) can select and push
-- them.

ALTER TABLE campaign_batches
    ADD COLUMN IF NOT EXISTS business_model        text,
    ADD COLUMN IF NOT EXISTS company_revenue       text,
    ADD COLUMN IF NOT EXISTS multi_entity          boolean,
    ADD COLUMN IF NOT EXISTS tam_segment           text,
    ADD COLUMN IF NOT EXISTS icp_archetype_primary   text,
    ADD COLUMN IF NOT EXISTS icp_archetype_secondary text,
    ADD COLUMN IF NOT EXISTS icp_archetype_evidence  text,
    ADD COLUMN IF NOT EXISTS tech_score            int,
    ADD COLUMN IF NOT EXISTS tech_stack_primary    text,
    ADD COLUMN IF NOT EXISTS tech_category         text,
    ADD COLUMN IF NOT EXISTS tech_esp              text,
    ADD COLUMN IF NOT EXISTS tech_crm              text,
    ADD COLUMN IF NOT EXISTS tech_cms              text,
    ADD COLUMN IF NOT EXISTS tech_ecommerce        text,
    ADD COLUMN IF NOT EXISTS tech_analytics        text,
    ADD COLUMN IF NOT EXISTS tech_cdn              text,
    ADD COLUMN IF NOT EXISTS tech_payment          text,
    ADD COLUMN IF NOT EXISTS tech_marketing        text,
    ADD COLUMN IF NOT EXISTS tech_chat             text,
    ADD COLUMN IF NOT EXISTS tech_hosting          text,
    ADD COLUMN IF NOT EXISTS tech_ab_testing       text,
    ADD COLUMN IF NOT EXISTS tech_tag_manager      text;
