-- Track when Phase 1 was launched for each gap row.  Used by run_phase1 to
-- enforce PhantomBuster's 150 LinkedIn-Company-Extractor launches/day limit.
ALTER TABLE contact_gaps
    ADD COLUMN IF NOT EXISTS phase1_launched_at timestamptz;

CREATE INDEX IF NOT EXISTS contact_gaps_phase1_launched_at
    ON contact_gaps (phase1_launched_at)
    WHERE phase1_launched_at IS NOT NULL;
