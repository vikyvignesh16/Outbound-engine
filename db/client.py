from supabase import create_client, Client
import asyncpg
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

async def get_pg():
    return await asyncpg.connect(os.environ["SUPABASE_DB_URL"], ssl="require")
