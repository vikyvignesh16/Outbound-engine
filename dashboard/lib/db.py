"""Read-only Supabase Postgres helper for the Streamlit dashboard.

Uses the direct Postgres connection (SUPABASE_DB_URL) so we can run rich
analytical queries with joins/aggregations rather than going through
PostgREST. Cached at module level with Streamlit's @st.cache_resource so a
single connection is shared across reruns, and individual query results are
cached with @st.cache_data for 5 minutes to keep the dashboard responsive
without hammering the database.

Secrets needed in Streamlit Community Cloud (Settings → Secrets):
    SUPABASE_DB_URL = "postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres"
    APP_PASSWORD    = "<some-shared-password>"        # gate at the top of streamlit_app.py
"""
import streamlit as st
import psycopg2
import pandas as pd


@st.cache_resource
def get_conn():
    """One Postgres connection per Streamlit session (shared across reruns)."""
    return psycopg2.connect(st.secrets["SUPABASE_DB_URL"], sslmode="require")


@st.cache_data(ttl=300, show_spinner=False)
def query_df(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Run a SELECT, return as DataFrame. Results cached for 5 minutes."""
    conn = get_conn()
    # If the cached connection went stale (idle disconnect), reconnect
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        get_conn.clear()
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)


def scalar(sql: str, params: tuple | None = None):
    """Run a SELECT that returns a single value."""
    df = query_df(sql, params)
    return df.iloc[0, 0] if not df.empty else None
