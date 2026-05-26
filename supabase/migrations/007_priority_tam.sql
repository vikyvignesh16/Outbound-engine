CREATE TABLE IF NOT EXISTS priority_tam (
    id                   uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    domain               text NOT NULL,
    market               text NOT NULL,
    company_name         text,
    brevo_company_id     text,
    planhat_id           text,
    open_deals           int,
    deal_lost_date       date,
    vertical             text,
    esp_detected         text,
    esp_score            int,
    account_fit_score    int CHECK (account_fit_score BETWEEN 1 AND 5),
    account_narrative    text,
    email_crm_activity   text,
    has_wallet           boolean DEFAULT false,
    has_loyalty_program  boolean DEFAULT false,
    needs_cdp            boolean DEFAULT false,
    prioritized_at       timestamptz DEFAULT now(),
    updated_at           timestamptz DEFAULT now(),
    UNIQUE (domain, market)
);

CREATE INDEX IF NOT EXISTS priority_tam_fit_idx    ON priority_tam (account_fit_score DESC);
CREATE INDEX IF NOT EXISTS priority_tam_market_idx ON priority_tam (market);
