CREATE TABLE IF NOT EXISTS hot_signals (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    domain              text        UNIQUE NOT NULL,
    company_name        text,
    market              text,
    clicks_count        int         DEFAULT 0,
    replies_count       int         DEFAULT 0,
    high_intent_visits  int         DEFAULT 0,
    opens_count         int         DEFAULT 0,
    last_signal_source  text,
    last_signal_at      timestamptz,
    pipeline_status     text        DEFAULT 'not_in_pipeline',
    pushed_to_leads     boolean     DEFAULT false,
    pushed_at           timestamptz,
    created_at          timestamptz DEFAULT now(),
    updated_at          timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS hot_signals_pipeline_status_idx  ON hot_signals (pipeline_status);
CREATE INDEX IF NOT EXISTS hot_signals_pushed_to_leads_idx  ON hot_signals (pushed_to_leads);
CREATE INDEX IF NOT EXISTS hot_signals_updated_at_idx       ON hot_signals (updated_at DESC);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_hot_signals_updated_at
    BEFORE UPDATE ON hot_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
