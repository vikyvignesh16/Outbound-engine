-- Raw PhantomBuster output — one row per scraped contact, before relevance scoring.
-- poll_phase2 writes here directly. The daily scoring cron reads unscored rows,
-- submits them to Claude in a single batch, and promotes score >= 3 to sourced_contacts.
CREATE TABLE IF NOT EXISTS phantombuster_contacts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scraped_at      timestamptz NOT NULL DEFAULT now(),
    batch_number    int  NOT NULL,
    domain          text NOT NULL,
    company_name    text,
    market          text,
    first_name      text,
    last_name       text,
    job_title       text,
    linkedin_url    text,
    email           text,
    raw             jsonb,
    -- Filled by /pipelines/score-contacts
    relevance_score     int,                  -- 1-5 per the ICP rubric
    relevance_reasoning text,
    scored_at           timestamptz,
    promoted_to_sourced_contacts boolean NOT NULL DEFAULT false,
    UNIQUE (domain, linkedin_url, batch_number)
);

CREATE INDEX IF NOT EXISTS phantombuster_contacts_unscored
    ON phantombuster_contacts (batch_number) WHERE scored_at IS NULL;

CREATE INDEX IF NOT EXISTS phantombuster_contacts_unpromoted
    ON phantombuster_contacts (batch_number)
    WHERE scored_at IS NOT NULL AND promoted_to_sourced_contacts = false;
