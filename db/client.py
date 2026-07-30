from supabase import create_client, Client
import os

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _supabase

# Convenience alias used across the codebase
supabase = get_supabase


def fetch_all(
    table: str,
    select: str,
    filters: list | None = None,
    limit: int | None = None,
    order_by: list[tuple[str, bool]] | None = None,
) -> list[dict]:
    """Paginate through rows in a table using supabase-py .range(). Pass limit to cap total rows.
    order_by: list of (column, desc) tuples applied consistently across pages.

    PostgREST does not guarantee stable row order across separate paginated
    requests without an explicit ORDER BY — over many pages this can silently
    skip or duplicate rows between fetches. Default to ordering by "id" so
    pagination is deterministic even when the caller doesn't specify a sort.
    """
    sb = get_supabase()
    all_rows: list[dict] = []
    page_size = 1000
    offset = 0
    # Always end with an "id" tiebreaker — a caller-supplied order_by on
    # non-unique columns (e.g. account_fit_score, prioritized_at) leaves ties
    # unstably ordered across separate paginated requests, which silently
    # duplicates or skips rows between pages. Appending id (unless already
    # present) preserves the caller's primary sort while making pagination
    # itself deterministic.
    effective_order_by = order_by or [("id", False)]
    if order_by and not any(col == "id" for col, _ in order_by):
        effective_order_by = [*order_by, ("id", False)]
    while True:
        remaining = (limit - len(all_rows)) if limit else page_size
        batch_size = min(page_size, remaining)
        query = sb.table(table).select(select).range(offset, offset + batch_size - 1)
        if filters:
            for method, *args in filters:
                query = getattr(query, method)(*args)
        for col, desc in effective_order_by:
            query = query.order(col, desc=desc)
        batch = query.execute().data
        all_rows.extend(batch)
        if len(batch) < batch_size or (limit and len(all_rows) >= limit):
            break
        offset += batch_size
    return all_rows
