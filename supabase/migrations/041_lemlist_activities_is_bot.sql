-- Promote Lemlist's `bot` boolean from raw_payload jsonb into a first-class
-- column so dashboards and queries can filter by human-vs-bot trivially
-- without parsing JSON every time.
--
-- Lemlist stamps `bot: true/false` on every emailsClicked and emailsOpened
-- event based on their internal heuristics (user-agent, IP reputation,
-- click timing, etc.). On the UKI ABM v2 campaign it caught 21% of click
-- events as bots (security scanners pre-clicking tracked links) — meaningful
-- inflation if you read raw click counts.
--
-- Backfill from existing rows in the same migration so every historical
-- event also gets its is_bot stamped.

ALTER TABLE lemlist_activities
    ADD COLUMN IF NOT EXISTS is_bot boolean;

CREATE INDEX IF NOT EXISTS lemlist_activities_is_bot_idx
    ON lemlist_activities (is_bot) WHERE is_bot IS NOT NULL;

UPDATE lemlist_activities
SET is_bot = (raw_payload->>'bot')::boolean
WHERE raw_payload ? 'bot'
  AND is_bot IS NULL;
