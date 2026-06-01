SELECT
    batch_id,
    model,
    status,
    companies_submitted,
    companies_enriched,
    input_tokens,
    output_tokens,
    estimated_cost_usd,
    submitted_at,
    completed_at
FROM {{ source('public', 'enrichment_batches') }}
