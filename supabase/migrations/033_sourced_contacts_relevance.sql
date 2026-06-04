-- Track the Claude relevance score on contacts that were promoted from
-- phantombuster_contacts.  Clay-sourced rows keep these columns NULL.
ALTER TABLE sourced_contacts
    ADD COLUMN IF NOT EXISTS relevance_score     int,
    ADD COLUMN IF NOT EXISTS relevance_reasoning text;
