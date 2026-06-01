SELECT
    market,
    COALESCE(vertical, 'unknown')  AS vertical,
    account_fit_score,
    has_wallet,
    has_loyalty_program,
    needs_cdp,
    COUNT(*)                       AS company_count
FROM {{ ref('stg_priority_tam') }}
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY market, account_fit_score DESC
