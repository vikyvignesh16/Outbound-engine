ALTER TABLE campaign_batches
    ADD COLUMN IF NOT EXISTS contacts_sourced_count  int,
    ADD COLUMN IF NOT EXISTS contacts_sourced_source text;
-- contacts_sourced_source values: 'clay' | 'linkedin' | 'clay+linkedin' | 'none'
