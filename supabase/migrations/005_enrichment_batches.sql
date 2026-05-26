CREATE TABLE IF NOT EXISTS enrichment_batches (
    id                   uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id             text UNIQUE NOT NULL,
    model                text NOT NULL,
    status               text NOT NULL DEFAULT 'pending',
    companies_submitted  int,
    companies_enriched   int,
    input_tokens         bigint,
    output_tokens        bigint,
    estimated_cost_usd   numeric(10, 6),
    submitted_at         timestamptz DEFAULT now(),
    completed_at         timestamptz
);

CREATE INDEX IF NOT EXISTS enrichment_batches_submitted_at_idx ON enrichment_batches (submitted_at DESC);
