-- sourced_tam_v2: swap unique constraint to include company_name
ALTER TABLE sourced_tam_v2 DROP CONSTRAINT IF EXISTS sourced_tam_v2_domain_market_key;
ALTER TABLE sourced_tam_v2 ADD CONSTRAINT sourced_tam_v2_domain_market_name_key
    UNIQUE (domain, market, company_name);

-- qualified_tam_v2
ALTER TABLE qualified_tam_v2 DROP CONSTRAINT IF EXISTS qualified_tam_v2_domain_market_key;
ALTER TABLE qualified_tam_v2 ADD CONSTRAINT qualified_tam_v2_domain_market_name_key
    UNIQUE (domain, market, company_name);

-- priority_tam
ALTER TABLE priority_tam DROP CONSTRAINT IF EXISTS priority_tam_domain_market_key;
ALTER TABLE priority_tam ADD CONSTRAINT priority_tam_domain_market_name_key
    UNIQUE (domain, market, company_name);

-- campaign_batches
ALTER TABLE campaign_batches DROP CONSTRAINT IF EXISTS campaign_batches_domain_market_key;
ALTER TABLE campaign_batches ADD CONSTRAINT campaign_batches_domain_market_name_key
    UNIQUE (domain, market, company_name);

-- enrichment_batches: add request_mapping for hash→company lookup
ALTER TABLE enrichment_batches
    ADD COLUMN IF NOT EXISTS request_mapping jsonb DEFAULT '{}';
