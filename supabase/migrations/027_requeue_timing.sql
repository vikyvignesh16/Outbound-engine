CREATE TABLE IF NOT EXISTS requeue_timing (
    id                       uuid  DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_email            text  NOT NULL,
    domain                   text  NOT NULL,
    company_name             text,
    reply_classification_id  uuid,
    requeue_date             date,
    requeue_reason           text,
    status                   text  DEFAULT 'pending',
    created_at               timestamptz DEFAULT now(),
    UNIQUE (contact_email, domain)
);

CREATE INDEX IF NOT EXISTS requeue_timing_status_idx        ON requeue_timing (status);
CREATE INDEX IF NOT EXISTS requeue_timing_requeue_date_idx  ON requeue_timing (requeue_date);
CREATE INDEX IF NOT EXISTS requeue_timing_domain_idx        ON requeue_timing (domain);
