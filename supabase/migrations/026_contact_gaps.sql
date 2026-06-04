CREATE TABLE IF NOT EXISTS contact_gaps (
    id                    uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    domain                text        NOT NULL,
    company_name          text,
    market                text,
    batch_number          int,
    gap_reason            text,
    phantombuster_status  text        DEFAULT 'pending',
    phantom_id            text,
    contacts_found        int,
    triggered_at          timestamptz DEFAULT now(),
    completed_at          timestamptz,
    UNIQUE (domain, batch_number)
);

CREATE INDEX IF NOT EXISTS contact_gaps_phantombuster_status_idx  ON contact_gaps (phantombuster_status);
CREATE INDEX IF NOT EXISTS contact_gaps_gap_reason_idx            ON contact_gaps (gap_reason);
CREATE INDEX IF NOT EXISTS contact_gaps_domain_idx                ON contact_gaps (domain);
