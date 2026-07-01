-- 046_contact_gaps_pb_failure_count.sql
--
-- Adds a retry counter so we can tell "PB flake" apart from "URL genuinely
-- dead / unclaimed". Discovered 2026-07-01 during UK gifting batch #2:
-- 39 rows failed PB Company Extractor with `{"error":"Unavailable company"}`,
-- got tagged linkedin_url_dead, ran through Claude URL-recovery. Manual
-- spot-checks (Menarys, Joules, Maidenhead) showed those LinkedIn pages
-- are LIVE — PB itself flaked (session / rate limit / anti-bot).
--
-- New failure handling (see pipelines/contact_gaps.py::poll_phase1):
--   • Empty PB result → increment pb_failure_count, reset status to 'pending'
--   • pb_failure_count >= 3 → tag 'linkedin_url_dead', pass to Claude recovery
--   • Recovery finds different URL → reset counter to 0
--   • Recovery returns SAME URL → archive with reason 'pb_persistent_failure'

ALTER TABLE contact_gaps
    ADD COLUMN IF NOT EXISTS pb_failure_count INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN contact_gaps.pb_failure_count IS
    'Consecutive PB Company Extractor empty-result failures for the CURRENT '
    'sourced_tam_v2.linkedin_url. Reset to 0 when Claude recovery finds a '
    'different URL. Reaching 3 hands the row off to linkedin_url_dead.';
