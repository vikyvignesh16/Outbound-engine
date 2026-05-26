CREATE TABLE IF NOT EXISTS campaign_batches (
    id                uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    domain            text NOT NULL,
    market            text NOT NULL,
    company_name      text,
    account_fit_score int,
    vertical          text,
    batch_number      int NOT NULL,
    batch_month       date NOT NULL,
    selected_at       timestamptz DEFAULT now(),
    UNIQUE (domain, market)
);

CREATE INDEX IF NOT EXISTS campaign_batches_month_idx  ON campaign_batches (batch_month DESC);
CREATE INDEX IF NOT EXISTS campaign_batches_number_idx ON campaign_batches (batch_number);
CREATE INDEX IF NOT EXISTS campaign_batches_market_idx ON campaign_batches (market);
