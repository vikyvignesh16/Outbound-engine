CREATE TABLE IF NOT EXISTS lead_routing (
    id             uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    domain         text        UNIQUE NOT NULL,
    company_name   text,
    market         text,
    contact_email  text,
    contact_name   text,
    job_title      text,
    signal_type    text,
    signal_detail  jsonb,
    triggered_at   timestamptz,
    status         text        DEFAULT 'new',
    notes          text,
    reviewed_at    timestamptz,
    created_at     timestamptz DEFAULT now(),
    updated_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS lead_routing_status_idx        ON lead_routing (status);
CREATE INDEX IF NOT EXISTS lead_routing_triggered_at_idx  ON lead_routing (triggered_at DESC);
CREATE INDEX IF NOT EXISTS lead_routing_domain_idx        ON lead_routing (domain);

CREATE TRIGGER update_lead_routing_updated_at
    BEFORE UPDATE ON lead_routing
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
