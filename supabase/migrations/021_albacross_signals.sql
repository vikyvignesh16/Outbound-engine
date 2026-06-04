CREATE TABLE IF NOT EXISTS albacross_signals (
    id                 uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    domain             text,
    company_name       text,
    country            text,
    market             text,
    pages_high_intent  jsonb,
    pages_visited      int,
    visits             int,
    unique_7_days      int,
    unique_30_days     int,
    unique_90_days     int,
    last_visit         timestamptz,
    duration           int,
    segment_name       text,
    utms               jsonb,
    raw_payload        jsonb,
    received_at        timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS albacross_signals_domain_idx       ON albacross_signals (domain);
CREATE INDEX IF NOT EXISTS albacross_signals_received_at_idx  ON albacross_signals (received_at DESC);
CREATE INDEX IF NOT EXISTS albacross_signals_market_idx       ON albacross_signals (market);
