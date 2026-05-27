ALTER TABLE sourced_tam_v2 ADD COLUMN IF NOT EXISTS crm_checked boolean DEFAULT false;
CREATE INDEX IF NOT EXISTS sourced_tam_v2_crm_checked_idx ON sourced_tam_v2 (crm_checked, market);
