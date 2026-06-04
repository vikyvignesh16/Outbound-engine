CREATE TABLE IF NOT EXISTS reply_classifications (
    id                   uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_email        text,
    domain               text,
    company_name         text,
    campaign_id          text,
    campaign_name        text,
    reply_content        text,
    classification       text,
    confidence           numeric,
    reasoning            text,
    action_taken         text,
    requeue_date         date,
    raw_lemlist_payload  jsonb,
    created_at           timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS reply_classifications_classification_idx  ON reply_classifications (classification);
CREATE INDEX IF NOT EXISTS reply_classifications_domain_idx          ON reply_classifications (domain);
CREATE INDEX IF NOT EXISTS reply_classifications_contact_email_idx   ON reply_classifications (contact_email);
CREATE INDEX IF NOT EXISTS reply_classifications_created_at_idx      ON reply_classifications (created_at DESC);
