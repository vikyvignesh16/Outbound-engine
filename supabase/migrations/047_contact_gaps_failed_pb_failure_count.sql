-- 047_contact_gaps_failed_pb_failure_count.sql
--
-- Migration 046 added pb_failure_count to contact_gaps but not to the archive
-- table contact_gaps_failed. Recovery's archive branch tries to INSERT the
-- whole contact_gaps row into contact_gaps_failed and now crashes because
-- pb_failure_count doesn't exist on the destination — Campanile and Nightcap
-- (batch #2, 2026-07-02) landed in this trap and got silently stuck at
-- linkedin_url_dead instead of moving to the archive.
--
-- Fix: mirror the column so contact_gaps_failed can accept the payload.

ALTER TABLE contact_gaps_failed
    ADD COLUMN IF NOT EXISTS pb_failure_count INT NOT NULL DEFAULT 0;
