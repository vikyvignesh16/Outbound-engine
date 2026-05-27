ALTER TABLE sourced_tam_v2
    DROP COLUMN IF EXISTS qualified,
    DROP COLUMN IF EXISTS disqualification_reason,
    DROP COLUMN IF EXISTS esp_detected,
    DROP COLUMN IF EXISTS esp_score,
    DROP COLUMN IF EXISTS account_fit_score,
    DROP COLUMN IF EXISTS account_narrative;
