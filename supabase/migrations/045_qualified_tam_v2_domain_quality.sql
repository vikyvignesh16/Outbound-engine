-- Domain Quality Agent — schema additions.
--
-- Runs every 6 hours via Railway cron on qualified_tam_v2. For each row not
-- yet checked, an agent (Claude Haiku 4.5 + web_search) determines:
--   1. Is the domain bogus (careers portal, gov service, social media, etc.)?
--   2. If bogus, what is the company's actual primary website?
--   3. If domain is shared with sibling companies in qualified_tam_v2, is this
--      row a Regional/Country HQ (keep + contact) or a property/branch/
--      franchisee (flag + skip — head office gets contacted instead)?
--
-- Verdict columns:
--   domain_status: verified | bogus | subsidiary | corrected
--   domain_role:   regional_hq | country_hq | property | branch | franchisee | independent
--   parent_company_name: name of the head-office entity (if subsidiary)
--   domain_corrected_to: the new domain if we recovered from a bogus one
--   domain_quality_checked_at: when the agent last ran on this row

ALTER TABLE qualified_tam_v2
    ADD COLUMN IF NOT EXISTS domain_status             TEXT,
    ADD COLUMN IF NOT EXISTS domain_role               TEXT,
    ADD COLUMN IF NOT EXISTS parent_company_name       TEXT,
    ADD COLUMN IF NOT EXISTS domain_corrected_to       TEXT,
    ADD COLUMN IF NOT EXISTS domain_quality_checked_at TIMESTAMPTZ;

ALTER TABLE qualified_tam_v2
    DROP CONSTRAINT IF EXISTS qualified_tam_v2_domain_status_check;
ALTER TABLE qualified_tam_v2
    ADD CONSTRAINT qualified_tam_v2_domain_status_check
    CHECK (domain_status IS NULL OR domain_status IN
        ('verified', 'bogus', 'subsidiary', 'corrected', 'unverified'));

ALTER TABLE qualified_tam_v2
    DROP CONSTRAINT IF EXISTS qualified_tam_v2_domain_role_check;
ALTER TABLE qualified_tam_v2
    ADD CONSTRAINT qualified_tam_v2_domain_role_check
    CHECK (domain_role IS NULL OR domain_role IN
        ('regional_hq', 'country_hq', 'global_hq', 'property', 'branch', 'franchisee', 'independent'));

CREATE INDEX IF NOT EXISTS qualified_tam_v2_domain_quality_checked_at_idx
    ON qualified_tam_v2 (domain_quality_checked_at NULLS FIRST);
