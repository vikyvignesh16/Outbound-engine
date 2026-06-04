CREATE TABLE IF NOT EXISTS blacklist (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    email               text        UNIQUE NOT NULL,
    domain              text,
    company_name        text,
    reason              text,
    source              text,
    lemlist_removed     boolean     DEFAULT false,
    lemlist_removed_at  timestamptz,
    raw_event           jsonb,
    created_at          timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS blacklist_domain_idx  ON blacklist (domain);
CREATE INDEX IF NOT EXISTS blacklist_reason_idx  ON blacklist (reason);
CREATE INDEX IF NOT EXISTS blacklist_source_idx  ON blacklist (source);
