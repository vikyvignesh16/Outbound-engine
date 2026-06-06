-- Add a separate seniority dimension (1-5) so promotion can tie-break by seniority
-- when many contacts at the same domain pass the relevance threshold (>=3).
--
-- Rubric (set by score_contacts.py):
--   5 = C-suite / Head-of (Head of CRM, CMO, Chief Marketing Officer)
--   4 = Director / VP
--   3 = Senior Manager / Lead
--   2 = Manager
--   1 = Executive / IC / Coordinator / Assistant
ALTER TABLE phantombuster_contacts
    ADD COLUMN IF NOT EXISTS seniority_score int;

ALTER TABLE sourced_contacts
    ADD COLUMN IF NOT EXISTS seniority_score int;
