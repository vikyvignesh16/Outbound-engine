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


def fetch_all(table: str, select: str, filters: list | None = None) -> list[dict]:
    """Paginate through all rows in a table using supabase-py .range()."""
    sb = get_supabase()
    all_rows: list[dict] = []
    page_size = 1000
    offset = 0
    while True:
        query = sb.table(table).select(select).range(offset, offset + page_size - 1)
        if filters:
            for method, *args in filters:
                query = getattr(query, method)(*args)
        batch = query.execute().data
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return all_rows
