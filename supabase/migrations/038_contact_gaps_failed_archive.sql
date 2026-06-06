-- Dead-letter table for contact_gaps rows that hit terminal data-quality
-- dead ends and need manual intervention (not pipeline retry).
--
-- Two buckets land here:
--   1. phantombuster_status='failed'             — PB Company Extractor errored,
--                                                  usually because the LinkedIn
--                                                  URL in sourced_tam_v2 is wrong,
--                                                  defunct, or points to a
--                                                  sub-property instead of the
--                                                  parent (e.g. one Lush spa
--                                                  location, not "Lush Ltd").
--   2. phantombuster_status='subsidiary_skipped' — pre-emptively skipped because
--                                                  the linkedin_url matched
--                                                  another company in the batch
--                                                  (subsidiary detection).
--
-- Neither is actively processed (run_phase1 only picks 'pending'), but they
-- clutter contact_gaps. Moving them here gives a single place to triage
-- URL fixes and keeps the active queue (pending / extracting / building /
-- scraping / completed / no_contacts_found) clean.
--
-- Same column set as contact_gaps, plus archived_at to record when each
-- row was moved out. Pure archival — nothing reads from this table in the
-- pipeline.

CREATE TABLE IF NOT EXISTS contact_gaps_failed (
    id                    uuid PRIMARY KEY,
    domain                text,
    company_name          text,
    market                text,
    batch_number          integer,
    gap_reason            text,
    phantombuster_status  text,
    phantom_id            text,
    contacts_found        integer,
    triggered_at          timestamptz,
    completed_at          timestamptz,
    linkedin_company_id   text,
    sales_nav_url         text,
    phase                 integer,
    phase1_launched_at    timestamptz,
    archived_at           timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contact_gaps_failed_domain_idx
    ON contact_gaps_failed (domain);

CREATE INDEX IF NOT EXISTS contact_gaps_failed_archived_at_idx
    ON contact_gaps_failed (archived_at);
