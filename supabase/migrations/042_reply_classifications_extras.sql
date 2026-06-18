-- Reply intelligence enrichments to reply_classifications.
--
-- lemlist_activity_id: the source lemlist_activities row's UUID, made unique
-- so the classifier is idempotent — if a reply has already been processed,
-- a second run is a no-op rather than a duplicate insert.
--
-- Three new entity-extraction columns the Claude classifier can populate:
--   referral_email       — "talk to sarah@x.com" type referrals
--   referral_name        — "talk to Sarah in marketing"
--   mentioned_competitor — "we already use Mailchimp" / "looking at Klaviyo"

ALTER TABLE reply_classifications
    ADD COLUMN IF NOT EXISTS lemlist_activity_id  uuid,
    ADD COLUMN IF NOT EXISTS referral_email       text,
    ADD COLUMN IF NOT EXISTS referral_name        text,
    ADD COLUMN IF NOT EXISTS mentioned_competitor text;

CREATE UNIQUE INDEX IF NOT EXISTS reply_classifications_lemlist_activity_id_key
    ON reply_classifications (lemlist_activity_id)
    WHERE lemlist_activity_id IS NOT NULL;

GRANT ALL ON public.reply_classifications TO anon, authenticated, service_role, postgres;
