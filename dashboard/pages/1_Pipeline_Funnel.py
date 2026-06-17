"""Pipeline Funnel — TAM → qualified → priority → batched → sourced → content → CSV.

Shows where prospects are in our pipeline, by market, and where the
biggest drop-offs are.
"""
import streamlit as st
import plotly.express as px

from lib.db import query_df

if not st.session_state.get("authed"):
    st.warning("Please sign in via the home page.")
    st.stop()

st.set_page_config(page_title="Pipeline Funnel | ABM V2", layout="wide")
st.title("🌊 Pipeline Funnel")
st.caption("How prospects flow through the system. Live, cached 5 min.")


# ── Overall funnel ────────────────────────────────────────────────────────────

st.subheader("Funnel — totals across all markets")

funnel = query_df("""
SELECT 'Sourced TAM'                                                                        AS stage,
       (SELECT COUNT(*) FROM sourced_tam_v2)                                                AS count,
       1                                                                                    AS step
UNION ALL SELECT 'Qualified TAM',
       (SELECT COUNT(*) FROM qualified_tam_v2), 2
UNION ALL SELECT 'Priority TAM (fit ≥ 3)',
       (SELECT COUNT(*) FROM priority_tam), 3
UNION ALL SELECT 'In a batch (campaign_batches)',
       (SELECT COUNT(*) FROM campaign_batches), 4
UNION ALL SELECT 'Contacts sourced',
       (SELECT COUNT(*) FROM sourced_contacts WHERE batch_number IS NOT NULL), 5
UNION ALL SELECT 'Contacts with content',
       (SELECT COUNT(*) FROM sourced_contacts WHERE content_generated_at IS NOT NULL), 6
UNION ALL SELECT 'Contacts with personalised LP',
       (SELECT COUNT(*) FROM sourced_contacts
        WHERE outbound_content->>'personalised_lp_url' IS NOT NULL
          AND outbound_content->>'personalised_lp_url' <> ''), 7
ORDER BY step
""")

c1, c2 = st.columns([2, 1])
with c1:
    fig = px.funnel(funnel, x="count", y="stage", title="Pipeline stages")
    fig.update_layout(height=480)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.dataframe(funnel[["stage", "count"]], hide_index=True, use_container_width=True)


# ── TAM → priority by market ──────────────────────────────────────────────────

st.subheader("TAM → Priority by market")
by_market = query_df("""
WITH s AS (SELECT market, COUNT(*) n FROM sourced_tam_v2 GROUP BY market),
     q AS (SELECT market, COUNT(*) n FROM qualified_tam_v2 GROUP BY market),
     p AS (SELECT market, COUNT(*) n FROM priority_tam GROUP BY market)
SELECT s.market, s.n AS sourced, q.n AS qualified, p.n AS priority,
       ROUND(100.0 * p.n / NULLIF(s.n, 0), 1) AS priority_pct_of_sourced
FROM s
LEFT JOIN q USING (market)
LEFT JOIN p USING (market)
ORDER BY s.n DESC
""")
st.dataframe(by_market, hide_index=True, use_container_width=True)


# ── Per-batch progress ────────────────────────────────────────────────────────

st.subheader("Per-batch progress")
batches = query_df("""
WITH cb AS (
  SELECT batch_number, market, COUNT(*) AS total_companies
  FROM campaign_batches GROUP BY batch_number, market
),
covered AS (
  SELECT batch_number, market, COUNT(DISTINCT domain) AS companies_with_contacts
  FROM sourced_contacts WHERE batch_number IS NOT NULL
  GROUP BY batch_number, market
),
content_done AS (
  SELECT batch_number, COUNT(*) AS contacts_with_content
  FROM sourced_contacts WHERE content_generated_at IS NOT NULL
  GROUP BY batch_number
)
SELECT cb.batch_number,
       cb.market,
       cb.total_companies,
       COALESCE(c.companies_with_contacts, 0) AS companies_with_contacts,
       ROUND(100.0 * COALESCE(c.companies_with_contacts, 0) / NULLIF(cb.total_companies, 0), 1) AS coverage_pct,
       COALESCE(cd.contacts_with_content, 0) AS contacts_with_content
FROM cb
LEFT JOIN covered c ON cb.batch_number = c.batch_number AND cb.market = c.market
LEFT JOIN content_done cd ON cb.batch_number = cd.batch_number
ORDER BY cb.batch_number DESC, cb.market
""")
st.dataframe(batches, hide_index=True, use_container_width=True)


# ── Contact source split ──────────────────────────────────────────────────────

st.subheader("Contact source split (Clay vs PhantomBuster)")
sources = query_df("""
SELECT COALESCE(source, '(unknown)') AS source,
       batch_number,
       COUNT(*) AS contacts,
       COUNT(*) FILTER (WHERE email IS NOT NULL AND email <> '') AS with_email,
       COUNT(*) FILTER (WHERE email IS NULL OR email = '')       AS no_email
FROM sourced_contacts
WHERE batch_number IS NOT NULL
GROUP BY source, batch_number
ORDER BY batch_number DESC, source
""")
st.dataframe(sources, hide_index=True, use_container_width=True)
