"""Brevo ABM V2 — Operations Dashboard.

Home page. Sub-pages live in pages/ and Streamlit auto-discovers them in
the sidebar (numeric prefix controls order).

Deployed on Streamlit Community Cloud, reads from Supabase Postgres
read-only. See dashboard/README.md for setup.
"""
import streamlit as st

from lib.db import query_df

st.set_page_config(
    page_title="Brevo ABM V2 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Simple password gate ──────────────────────────────────────────────────────

def _check_password() -> bool:
    """Returns True if the user has entered the shared password."""
    if st.session_state.get("authed"):
        return True
    st.title("Brevo ABM V2 Dashboard")
    pw = st.text_input("Password", type="password")
    if pw and pw == st.secrets.get("APP_PASSWORD", ""):
        st.session_state["authed"] = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    return False


if not _check_password():
    st.stop()


# ── Landing page ──────────────────────────────────────────────────────────────

st.title("📊 Brevo ABM V2 — Operations Dashboard")
st.caption("Live data from Supabase. Cached for 5 min.")

st.markdown(
    """
    ### Navigate
    Use the sidebar to explore:

    - **Pipeline Funnel** — TAM → qualified → priority → batched → sourced → content → CSV
    - **Campaign Performance** — Lemlist engagement metrics, bot-filtered
    - **Operational Health** — pipeline backlogs, cache state, recent activity

    ---
    """
)

# Quick stats strip on the home page
st.subheader("Snapshot")

c1, c2, c3, c4 = st.columns(4)

with c1:
    n = query_df("SELECT COUNT(*) FROM sourced_tam_v2").iloc[0, 0]
    st.metric("Sourced TAM", f"{n:,}")

with c2:
    n = query_df("SELECT COUNT(*) FROM priority_tam").iloc[0, 0]
    st.metric("Priority TAM (fit ≥ 3)", f"{n:,}")

with c3:
    n = query_df("SELECT COUNT(*) FROM sourced_contacts WHERE batch_number IS NOT NULL").iloc[0, 0]
    st.metric("Contacts sourced (all batches)", f"{n:,}")

with c4:
    n = query_df(
        "SELECT COUNT(*) FROM sourced_contacts WHERE content_generated_at IS NOT NULL"
    ).iloc[0, 0]
    st.metric("Contacts with content", f"{n:,}")

st.markdown("---")
st.caption("Built with Streamlit. Source: github.com/vikyvignesh16/brevo-outbound-engine")
