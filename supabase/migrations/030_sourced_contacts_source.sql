ALTER TABLE sourced_contacts
    ADD COLUMN IF NOT EXISTS source text DEFAULT 'clay';
