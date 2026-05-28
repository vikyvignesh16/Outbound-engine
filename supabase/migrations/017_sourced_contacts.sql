CREATE TABLE IF NOT EXISTS sourced_contacts (
    id                     uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    domain                 text NOT NULL,
    email                  text,
    first_name             text,
    last_name              text,
    job_title              text,
    seniority              text,
    linkedin_url           text,
    company_name           text,
    market                 text,
    batch_number           int,
    outbound_subject       text,
    outbound_body          text,
    outbound_linkedin_note text,
    content_batch_id       text,
    content_generated_at   timestamptz,
    raw                    jsonb,
    created_at             timestamptz DEFAULT now(),
    UNIQUE (domain, email)
);

CREATE INDEX IF NOT EXISTS sourced_contacts_content_pending_idx
    ON sourced_contacts (content_generated_at) WHERE content_generated_at IS NULL;

CREATE INDEX IF NOT EXISTS sourced_contacts_batch_number_idx
    ON sourced_contacts (batch_number);
