CREATE TABLE IF NOT EXISTS contact_content_batches (
    id                   uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id             text UNIQUE NOT NULL,
    model                text NOT NULL,
    status               text NOT NULL DEFAULT 'pending',
    contacts_submitted   int,
    contacts_completed   int,
    input_tokens         bigint,
    output_tokens        bigint,
    estimated_cost_usd   numeric(10, 6),
    submitted_at         timestamptz DEFAULT now(),
    completed_at         timestamptz,
    request_mapping      jsonb DEFAULT '{}'
);
