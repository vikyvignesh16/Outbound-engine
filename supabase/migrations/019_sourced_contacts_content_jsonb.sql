ALTER TABLE sourced_contacts
    DROP COLUMN IF EXISTS outbound_subject,
    DROP COLUMN IF EXISTS outbound_body,
    DROP COLUMN IF EXISTS outbound_linkedin_note,
    ADD COLUMN IF NOT EXISTS outbound_content jsonb;
