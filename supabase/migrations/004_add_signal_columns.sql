ALTER TABLE qualified_tam_v2
    ADD COLUMN IF NOT EXISTS has_wallet          boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS has_loyalty_program boolean DEFAULT false,
    ADD COLUMN IF NOT EXISTS needs_cdp           boolean DEFAULT false;
