-- Switch the per-person uniqueness key from (domain, email) to linkedin_url.
--
-- The old (domain, email) constraint collided whenever multiple contacts at
-- the same domain had a NULL/empty email — which is exactly what made the
-- daily content batch crash on duplicate custom_ids (sha256(domain||"") was
-- identical across emailless contacts). LinkedIn URL is unique per person
-- regardless of email availability, so it's the right identifier.
--
-- The application normalises linkedin_url before insert: lowercased, with
-- scheme + "www." + trailing slash stripped, so cross-source variations like
-- "https://www.linkedin.com/in/foo/" (Clay) and "https://linkedin.com/in/foo"
-- (PhantomBuster) collapse to a single canonical form.

ALTER TABLE sourced_contacts
    DROP CONSTRAINT IF EXISTS sourced_contacts_domain_email_key;

ALTER TABLE sourced_contacts
    ADD CONSTRAINT sourced_contacts_linkedin_url_key UNIQUE (linkedin_url);
