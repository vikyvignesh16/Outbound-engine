-- Track which enrichment tool found each contact's email. Lets us spot which
-- providers deliver high-deliverability addresses vs which ones supply junk
-- when bounce-rates come back from Lemlist.
ALTER TABLE sourced_contacts
    ADD COLUMN IF NOT EXISTS email_provider text;
