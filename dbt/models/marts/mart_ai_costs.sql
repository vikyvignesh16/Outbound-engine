SELECT
    'enrichment'          AS batch_type,
    batch_id,
    model,
    status,
    companies_submitted   AS units_submitted,
    companies_enriched    AS units_completed,
    input_tokens,
    output_tokens,
    estimated_cost_usd,
    submitted_at,
    completed_at,
    DATE_TRUNC('day', submitted_at) AS day
FROM {{ ref('stg_enrichment_batches') }}

UNION ALL

SELECT
    'content'             AS batch_type,
    batch_id,
    model,
    status,
    contacts_submitted    AS units_submitted,
    contacts_completed    AS units_completed,
    input_tokens,
    output_tokens,
    estimated_cost_usd,
    submitted_at,
    completed_at,
    DATE_TRUNC('day', submitted_at) AS day
FROM {{ ref('stg_contact_content_batches') }}

ORDER BY submitted_at DESC
