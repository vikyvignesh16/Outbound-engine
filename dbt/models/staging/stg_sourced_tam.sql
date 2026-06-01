SELECT
    domain,
    market,
    company_name,
    company_type,
    employee_range,
    country,
    vertical,
    crm_checked,
    brevo_company_id,
    open_deals,
    deal_lost_date,
    planhat_id,
    created_at,
    updated_at
FROM {{ source('public', 'sourced_tam_v2') }}
