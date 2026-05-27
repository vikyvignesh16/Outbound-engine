-- Add missing sourced_tam_v2 columns to qualified_tam_v2
ALTER TABLE qualified_tam_v2
    ADD COLUMN IF NOT EXISTS company_type   text,
    ADD COLUMN IF NOT EXISTS employee_range text,
    ADD COLUMN IF NOT EXISTS location       text,
    ADD COLUMN IF NOT EXISTS country        text,
    ADD COLUMN IF NOT EXISTS linkedin_url   text;

-- Add same columns to priority_tam
ALTER TABLE priority_tam
    ADD COLUMN IF NOT EXISTS company_type   text,
    ADD COLUMN IF NOT EXISTS employee_range text,
    ADD COLUMN IF NOT EXISTS location       text,
    ADD COLUMN IF NOT EXISTS country        text,
    ADD COLUMN IF NOT EXISTS linkedin_url   text;

-- Add same columns to campaign_batches
ALTER TABLE campaign_batches
    ADD COLUMN IF NOT EXISTS company_type   text,
    ADD COLUMN IF NOT EXISTS employee_range text,
    ADD COLUMN IF NOT EXISTS location       text,
    ADD COLUMN IF NOT EXISTS country        text,
    ADD COLUMN IF NOT EXISTS linkedin_url   text;
