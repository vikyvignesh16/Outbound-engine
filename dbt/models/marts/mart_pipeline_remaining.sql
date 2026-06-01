SELECT
    p.market,
    COALESCE(p.vertical, 'unknown')  AS vertical,
    p.account_fit_score,
    COUNT(*)                         AS remaining_companies
FROM {{ ref('stg_priority_tam') }} p
WHERE NOT EXISTS (
    SELECT 1
    FROM {{ ref('stg_campaign_batches') }} cb
    WHERE cb.domain = p.domain
      AND cb.market = p.market
)
GROUP BY 1, 2, 3
ORDER BY p.market, p.account_fit_score DESC
