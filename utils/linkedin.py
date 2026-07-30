def normalise_linkedin_url(url: str | None) -> str:
    """Canonicalise a LinkedIn URL for cross-source dedup.

    Lowercases, drops https?:// + www. + trailing slash + query/fragment.
    e.g. "https://www.linkedin.com/in/Foo/" -> "linkedin.com/in/foo"

    Shared by webhooks/clay_contacts.py and scripts/import_clay_contacts.py
    so Clay's URL formatting and PhantomBuster's collapse to the same
    canonical form (sourced_contacts.linkedin_url is the unique dedup key).
    """
    u = (url or "").strip().lower()
    if not u:
        return ""
    for prefix in ("https://", "http://"):
        if u.startswith(prefix):
            u = u[len(prefix):]
            break
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/").split("?", 1)[0].split("#", 1)[0]
