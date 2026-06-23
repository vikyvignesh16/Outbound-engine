-- priority_tam_parked: side-table for rows we deliberately exclude from the
-- mass push because their domain is shared with at least one other priority_tam
-- row. Two kinds end up here:
--   1. Legitimate chain brands (Hilton/Marriott/IHG properties etc.) — each
--      property is a real distinct outreach target, but until RevOps tells us
--      how they want chain-shared website CRM records handled, we park them.
--   2. Clay-enrichment data quality bugs (allens.ie shared by 51 unrelated
--      companies, boots.jobs across 6, etc.) — domains are wrong, need fixing
--      before push.
--
-- Schema mirrors priority_tam exactly (LIKE ... INCLUDING ALL) plus two
-- bookkeeping columns: parked_reason and parked_at. Mass push reads only
-- priority_tam, so parking a row is the simplest way to exclude it.

CREATE TABLE IF NOT EXISTS priority_tam_parked (
    LIKE priority_tam INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING IDENTITY,
    parked_reason TEXT NOT NULL,
    parked_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
