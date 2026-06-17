"""Operational Health — pipeline backlogs, cache state, recent activity.

Shows the GTM-engineering view: what's queued, what's stuck, when things
last ran, and where the system might need attention.
"""
import streamlit as st
import plotly.express as px

from lib.db import query_df

if not st.session_state.get("authed"):
    st.warning("Please sign in via the home page.")
    st.stop()

st.set_page_config(page_title="Operational Health | ABM V2", layout="wide")
st.title("🔧 Operational Health")
st.caption("Backlogs, caches, last-run timestamps. 5-min cache.")


# ── Last activity per pipeline ────────────────────────────────────────────────

st.subheader("Last activity per pipeline (UTC)")

last = query_df("""
SELECT 'Enrichment batches'    AS pipeline,
       (SELECT COUNT(*) FROM enrichment_batches)        AS rows,
       (SELECT MAX(submitted_at) FROM enrichment_batches) AS last_run
UNION ALL SELECT 'Content batches',
       (SELECT COUNT(*) FROM contact_content_batches),
       (SELECT MAX(submitted_at) FROM contact_content_batches)
UNION ALL SELECT 'Contact gaps (active)',
       (SELECT COUNT(*) FROM contact_gaps),
       (SELECT MAX(triggered_at) FROM contact_gaps)
UNION ALL SELECT 'Contact gaps (archived)',
       (SELECT COUNT(*) FROM contact_gaps_failed),
       (SELECT MAX(archived_at) FROM contact_gaps_failed)
UNION ALL SELECT 'PhantomBuster contacts',
       (SELECT COUNT(*) FROM phantombuster_contacts),
       (SELECT MAX(scored_at) FROM phantombuster_contacts)
UNION ALL SELECT 'Albacross signals',
       (SELECT COUNT(*) FROM albacross_signals),
       (SELECT MAX(received_at) FROM albacross_signals)
UNION ALL SELECT 'Lemlist events',
       (SELECT COUNT(*) FROM lemlist_activities),
       (SELECT MAX(received_at) FROM lemlist_activities)
ORDER BY last_run DESC NULLS LAST
""")
st.dataframe(last, hide_index=True, use_container_width=True)


# ── PB pipeline state ─────────────────────────────────────────────────────────

st.subheader("PhantomBuster contact_gaps — by state")

pb = query_df("""
SELECT phantombuster_status, market, COUNT(*) AS rows
FROM contact_gaps
GROUP BY phantombuster_status, market
ORDER BY phantombuster_status, market
""")

if pb.empty:
    st.caption("No active contact_gaps rows.")
else:
    fig = px.bar(pb, x="phantombuster_status", y="rows", color="market",
                 title="Active contact_gaps by status × market", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pb, hide_index=True, use_container_width=True)

pb_dead = query_df("""
SELECT phantombuster_status, gap_reason, COUNT(*) AS rows
FROM contact_gaps_failed
GROUP BY phantombuster_status, gap_reason
ORDER BY rows DESC
""")
st.caption("Dead-lettered contact_gaps_failed (archived rows that won't be retried)")
st.dataframe(pb_dead, hide_index=True, use_container_width=True)


# ── Cache stats ───────────────────────────────────────────────────────────────

st.subheader("Per-domain caches")

c1, c2 = st.columns(2)
with c1:
    news = query_df("""
    SELECT COUNT(*)                                                   AS total,
           COUNT(*) FILTER (WHERE found AND usable)                   AS usable,
           COUNT(*) FILTER (WHERE NOT (found AND usable))             AS unusable
    FROM company_news_cache
    """)
    n = news.iloc[0]
    st.metric("News cache (domains)", f"{n['total']:,}",
              f"{n['usable']:,} usable / {n['unusable']:,} 'no news'")
with c2:
    lp = query_df("SELECT COUNT(*) AS total FROM company_lp_cache").iloc[0, 0]
    st.metric("LP cache (domains)", f"{lp:,}")


# ── Webhook health (rolling 14d) ──────────────────────────────────────────────

st.subheader("Webhook health — events per day (last 14d)")

c1, c2 = st.columns(2)

with c1:
    al = query_df("""
    SELECT DATE_TRUNC('day', received_at AT TIME ZONE 'UTC')::date AS day, COUNT(*) AS events
    FROM albacross_signals
    WHERE received_at >= NOW() - INTERVAL '14 days'
    GROUP BY day ORDER BY day
    """)
    fig = px.bar(al, x="day", y="events", title="Albacross events / day")
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    lm = query_df("""
    SELECT DATE_TRUNC('day', received_at AT TIME ZONE 'UTC')::date AS day, COUNT(*) AS events
    FROM lemlist_activities
    WHERE received_at >= NOW() - INTERVAL '14 days'
    GROUP BY day ORDER BY day
    """)
    fig = px.bar(lm, x="day", y="events", title="Lemlist events / day")
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)


# ── Pending work ──────────────────────────────────────────────────────────────

st.subheader("Pending work")

pending = query_df("""
SELECT 'PB contacts unscored'                                                                AS item,
       (SELECT COUNT(*) FROM phantombuster_contacts WHERE scored_at IS NULL)                 AS count
UNION ALL SELECT 'PB contacts scored but not promoted',
       (SELECT COUNT(*) FROM phantombuster_contacts
        WHERE scored_at IS NOT NULL AND promoted_to_sourced_contacts IS NOT TRUE)
UNION ALL SELECT 'Sourced contacts missing email + no LinkedIn',
       (SELECT COUNT(*) FROM sourced_contacts
        WHERE (email IS NULL OR email='') AND (linkedin_url IS NULL OR linkedin_url=''))
UNION ALL SELECT 'Sourced contacts missing content',
       (SELECT COUNT(*) FROM sourced_contacts WHERE content_generated_at IS NULL)
UNION ALL SELECT 'Sourced contacts missing personalised LP URL',
       (SELECT COUNT(*) FROM sourced_contacts
        WHERE outbound_content IS NOT NULL
          AND (outbound_content->>'personalised_lp_url' IS NULL OR outbound_content->>'personalised_lp_url'=''))
UNION ALL SELECT 'Content batches still pending',
       (SELECT COUNT(*) FROM contact_content_batches WHERE status='pending')
UNION ALL SELECT 'Enrichment batches still pending',
       (SELECT COUNT(*) FROM enrichment_batches WHERE status!='completed')
ORDER BY count DESC
""")
st.dataframe(pending, hide_index=True, use_container_width=True)
