CREATE TABLE sourced_tam (
    id                      uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    domain                  text NOT NULL,
    market                  text NOT NULL,
    company_name            text,
    company_type            text,
    employee_range          text,
    location                text,
    country                 text,
    linkedin_url            text,
    brevo_company_id        text,
    open_deals              int,
    deal_lost_date          date,
    vertical                text,
    clay_id                 text,
    -- Step 2-4: qualification (populated by pipelines/qualification.py)
    esp_detected            boolean,
    esp_score               numeric,
    qualified               boolean,
    disqualification_reason text,
    -- Step 5: AI enrichment (populated by pipelines/enrichment.py)
    account_fit_score       int CHECK (account_fit_score BETWEEN 1 AND 5),
    account_narrative       text,
    -- Metadata
    raw                     jsonb,
    created_at              timestamptz DEFAULT now(),
    updated_at              timestamptz DEFAULT now(),
    UNIQUE (domain, market)
);

CREATE INDEX sourced_tam_market_idx ON sourced_tam (market);
CREATE INDEX sourced_tam_fit_idx    ON sourced_tam (account_fit_score);
CREATE INDEX sourced_tam_qual_idx   ON sourced_tam (qualified);
