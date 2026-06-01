SELECT
    batch_number,
    DATE_TRUNC('month', batch_month::timestamp)  AS batch_month,
    market,
    COUNT(*)                                     AS companies_selected,
    COUNT(*) FILTER (WHERE clay_pushed_at IS NOT NULL) AS pushed_to_clay,
    COUNT(*) FILTER (WHERE clay_pushed_at IS NULL)     AS pending_push,
    ROUND(AVG(account_fit_score)::numeric, 2)    AS avg_fit_score,
    MIN(selected_at)                             AS first_selected_at,
    MAX(selected_at)                             AS last_selected_at
FROM {{ ref('stg_campaign_batches') }}
GROUP BY 1, 2, 3
ORDER BY batch_number, market
