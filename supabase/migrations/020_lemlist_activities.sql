CREATE TABLE IF NOT EXISTS lemlist_activities (
    id             uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_email     text,
    domain         text,
    company_name   text,
    campaign_id    text,
    campaign_name  text,
    lead_id        text,
    contact_id     text,
    event_type     text,
    sequence_step  int,
    raw_payload    jsonb,
    created_at     timestamptz,
    received_at    timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS lemlist_activities_event_type_idx         ON lemlist_activities (event_type);
CREATE INDEX IF NOT EXISTS lemlist_activities_domain_idx             ON lemlist_activities (domain);
CREATE INDEX IF NOT EXISTS lemlist_activities_domain_event_type_idx  ON lemlist_activities (domain, event_type);
CREATE INDEX IF NOT EXISTS lemlist_activities_received_at_idx        ON lemlist_activities (received_at DESC);
