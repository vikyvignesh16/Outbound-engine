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


def fetch_all(table: str, select: str, filters: list | None = None, limit: int | None = None) -> list[dict]:
    """Paginate through rows in a table using supabase-py .range(). Pass limit to cap total rows."""
    sb = get_supabase()
    all_rows: list[dict] = []
    page_size = 1000
    offset = 0
    while True:
        remaining = (limit - len(all_rows)) if limit else page_size
        batch_size = min(page_size, remaining)
        query = sb.table(table).select(select).range(offset, offset + batch_size - 1)
        if filters:
            for method, *args in filters:
                query = getattr(query, method)(*args)
        batch = query.execute().data
        all_rows.extend(batch)
        if len(batch) < batch_size or (limit and len(all_rows) >= limit):
            break
        offset += batch_size
    return all_rows
