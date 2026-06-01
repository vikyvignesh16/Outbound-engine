SELECT
    batch_id,
    model,
    status,
    contacts_submitted,
    contacts_completed,
    input_tokens,
    output_tokens,
    estimated_cost_usd,
    submitted_at,
    completed_at
FROM {{ source('public', 'contact_content_batches') }}
