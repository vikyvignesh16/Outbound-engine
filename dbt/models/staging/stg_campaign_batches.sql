SELECT
    domain,
    market,
    company_name,
    batch_number,
    batch_month,
    account_fit_score,
    vertical,
    has_wallet,
    has_loyalty_program,
    needs_cdp,
    selected_at,
    clay_pushed_at
FROM {{ source('public', 'campaign_batches') }}
