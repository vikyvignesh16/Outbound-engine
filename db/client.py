import ssl
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
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = os.environ["SUPABASE_DB_URL"].split("?")[0]  # strip sslmode query param
    return await asyncpg.connect(url, ssl=ctx)
