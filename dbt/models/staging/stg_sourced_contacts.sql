SELECT
    id,
    domain,
    email,
    first_name,
    last_name,
    job_title,
    seniority,
    company_name,
    market,
    batch_number,
    content_generated_at,
    content_batch_id,
    created_at
FROM {{ source('public', 'sourced_contacts') }}
