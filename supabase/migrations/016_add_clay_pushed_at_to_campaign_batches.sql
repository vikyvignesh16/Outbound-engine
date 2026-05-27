ALTER TABLE campaign_batches ADD COLUMN IF NOT EXISTS clay_pushed_at timestamptz;
CREATE INDEX IF NOT EXISTS campaign_batches_clay_pushed_idx ON campaign_batches (clay_pushed_at) WHERE clay_pushed_at IS NULL;
