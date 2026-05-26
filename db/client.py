from supabase import create_client
import asyncpg
import os

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

async def get_pg():
    return await asyncpg.connect(os.environ["SUPABASE_DB_URL"])
