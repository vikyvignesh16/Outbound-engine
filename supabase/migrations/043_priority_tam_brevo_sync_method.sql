-- Records which Brevo CRM sync path was taken for each priority_tam row.
--
--   'POST'  → row was created in Brevo CRM (no brevo_company_id existed)
--   'PATCH' → row was updated in Brevo CRM (brevo_company_id already present)
--   NULL    → row has never been synced
--
-- Combined with brevo_company_id, this gives us an audit trail of every row's
-- last sync action and lets re-runs route the same row to PATCH on subsequent
-- passes (no duplicates).

ALTER TABLE priority_tam
    ADD COLUMN IF NOT EXISTS brevo_sync_method TEXT;

ALTER TABLE priority_tam
    DROP CONSTRAINT IF EXISTS priority_tam_brevo_sync_method_check;

ALTER TABLE priority_tam
    ADD CONSTRAINT priority_tam_brevo_sync_method_check
    CHECK (brevo_sync_method IS NULL OR brevo_sync_method IN ('POST', 'PATCH'));
