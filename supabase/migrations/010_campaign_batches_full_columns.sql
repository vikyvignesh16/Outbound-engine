ALTER TABLE campaign_batches
    ADD COLUMN IF NOT EXISTS brevo_company_id   text,
    ADD COLUMN IF NOT EXISTS planhat_id         text,
    ADD COLUMN IF NOT EXISTS open_deals         int,
    ADD COLUMN IF NOT EXISTS deal_lost_date     date,
    ADD COLUMN IF NOT EXISTS esp_detected       text,
    ADD COLUMN IF NOT EXISTS esp_score          int,
    ADD COLUMN IF NOT EXISTS account_narrative  text,
    ADD COLUMN IF NOT EXISTS email_crm_activity text,
    ADD COLUMN IF NOT EXISTS has_wallet         boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS has_loyalty_program boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS needs_cdp          boolean DEFAULT false;
