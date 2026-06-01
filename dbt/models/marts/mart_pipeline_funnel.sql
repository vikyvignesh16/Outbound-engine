WITH sourced AS (
    SELECT
        market,
        COUNT(*)                               AS sourced_total,
        COUNT(*) FILTER (WHERE crm_checked)    AS crm_checked
    FROM {{ ref('stg_sourced_tam') }}
    GROUP BY 1
),

qualified AS (
    SELECT market, COUNT(*) AS qualified_total
    FROM {{ ref('stg_qualified_tam') }}
    GROUP BY 1
),

priority AS (
    SELECT market, COUNT(*) AS priority_total
    FROM {{ ref('stg_priority_tam') }}
    GROUP BY 1
),

batched AS (
    SELECT
        market,
        COUNT(*)                                             AS batched_total,
        COUNT(*) FILTER (WHERE clay_pushed_at IS NOT NULL)  AS pushed_to_clay
    FROM {{ ref('stg_campaign_batches') }}
    GROUP BY 1
),

contacts AS (
    SELECT
        market,
        COUNT(*)                                                   AS contacts_total,
        COUNT(*) FILTER (WHERE content_generated_at IS NOT NULL)   AS content_generated
    FROM {{ ref('stg_sourced_contacts') }}
    GROUP BY 1
)

SELECT
    s.market,
    s.sourced_total,
    s.crm_checked,
    COALESCE(q.qualified_total,  0) AS qualified_total,
    COALESCE(p.priority_total,   0) AS priority_total,
    COALESCE(b.batched_total,    0) AS batched_total,
    COALESCE(b.pushed_to_clay,   0) AS pushed_to_clay,
    COALESCE(c.contacts_total,   0) AS contacts_total,
    COALESCE(c.content_generated, 0) AS content_generated
FROM sourced s
LEFT JOIN qualified q ON s.market = q.market
LEFT JOIN priority  p ON s.market = p.market
LEFT JOIN batched   b ON s.market = b.market
LEFT JOIN contacts  c ON s.market = c.market
ORDER BY s.sourced_total DESC
