CREATE TABLE IF NOT EXISTS qualified_tam_v2 (
    id                  uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    domain              text NOT NULL,
    market              text NOT NULL,
    company_name        text,
    brevo_company_id    text,
    planhat_id          text,
    open_deals          int,
    deal_lost_date      date,
    vertical            text,
    esp_detected        text,
    esp_score           int,
    account_fit_score   int CHECK (account_fit_score BETWEEN 1 AND 5),
    account_narrative   text,
    sourced_at          timestamptz DEFAULT now(),
    updated_at          timestamptz DEFAULT now(),
    UNIQUE (domain, market)
);

CREATE INDEX IF NOT EXISTS qualified_tam_v2_fit_idx    ON qualified_tam_v2 (account_fit_score);
CREATE INDEX IF NOT EXISTS qualified_tam_v2_market_idx ON qualified_tam_v2 (market);
