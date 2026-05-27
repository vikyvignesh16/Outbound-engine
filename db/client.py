import ssl
import urllib.parse
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
    parsed = urllib.parse.urlparse(os.environ["SUPABASE_DB_URL"])
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=urllib.parse.unquote(parsed.password or ""),
        database=parsed.path.lstrip("/"),
        ssl=ctx,
    )
