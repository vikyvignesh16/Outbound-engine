ALTER TABLE contact_gaps
    ADD COLUMN IF NOT EXISTS linkedin_company_id  text,
    ADD COLUMN IF NOT EXISTS sales_nav_url         text,
    ADD COLUMN IF NOT EXISTS phase                 int DEFAULT 1;
