CREATE TABLE IF NOT EXISTS bounce_analysis (
    id                   uuid  DEFAULT gen_random_uuid() PRIMARY KEY,
    analysis_date        date  NOT NULL,
    total_bounces        int,
    by_source            jsonb,
    by_esp               jsonb,
    by_market            jsonb,
    patterns_identified  jsonb,
    created_at           timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bounce_analysis_analysis_date_idx  ON bounce_analysis (analysis_date DESC);
