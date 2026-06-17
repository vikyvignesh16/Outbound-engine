"""Bounce Analysis — diagnose why emails are bouncing on the UKI ABM v2 campaign.

Pulls every emailsBounced event for the active ABM campaign, parses the SMTP
response from the bounce notification text (raw_payload.text), and breaks
down by email_provider / sender / domain / bounce category.

The hard_recipient_not_found bucket is the one to watch — those are bad
addresses the enrichment source (Apollo/Lusha/manual) gave us.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from lib.db import query_df
from lib.bounce_parser import parse_bounce

if not st.session_state.get("authed"):
    st.warning("Please sign in via the home page.")
    st.stop()

st.set_page_config(page_title="Bounce Analysis | ABM V2", layout="wide")
st.title("📉 Bounce Analysis")
st.caption("UKI ABM v2 — Outbound Engine. Diagnose what's bouncing and why.")

CAMPAIGN_ID = "cam_cjkdYRBDEZFaXXYxo"


# ── Pull bounces + correlated context ─────────────────────────────────────────

bounces = query_df("""
SELECT la.lead_email,
       la.domain,
       la.company_name,
       la.received_at,
       la.raw_payload->>'text'         AS bounce_text,
       la.raw_payload->>'subject'      AS bounce_subject,
       la.raw_payload->>'sendUserName' AS sender,
       la.raw_payload->>'fromEmail'    AS bounce_from,
       sc.email_provider,
       sc.source                       AS contact_source
FROM lemlist_activities la
LEFT JOIN sourced_contacts sc ON sc.email = la.lead_email
WHERE la.campaign_id = %s
  AND la.event_type = 'emailsBounced'
ORDER BY la.received_at DESC
""", (CAMPAIGN_ID,))

if bounces.empty:
    st.info("No bounces yet for this campaign 🎉")
    st.stop()

# Pull sent total for the rate calc (unique leads sent to)
sent_total = query_df("""
SELECT COUNT(DISTINCT lead_email) AS n
FROM lemlist_activities
WHERE campaign_id = %s AND event_type = 'emailsSent'
""", (CAMPAIGN_ID,)).iloc[0, 0]


# ── Parse bounce text → category + severity + SMTP codes ──────────────────────

parsed = bounces["bounce_text"].apply(parse_bounce).apply(pd.Series)
bounces = pd.concat([bounces.drop(columns=["bounce_text"]), parsed], axis=1)


# ── Headline metrics ──────────────────────────────────────────────────────────

total = len(bounces)
hard = int((bounces["severity"] == "hard").sum())
soft = int((bounces["severity"] == "soft").sum())
unknown = int((bounces["severity"] == "unknown").sum())
bounce_rate = total / max(1, sent_total) * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total bounces",  f"{total:,}")
c2.metric("Unique sent",    f"{sent_total:,}")
c3.metric("Bounce rate",    f"{bounce_rate:.1f}%")
c4.metric("Hard / Soft",    f"{hard} / {soft}", f"{unknown} unclassified" if unknown else None)
c5.metric("Distinct domains affected", f"{bounces['domain'].nunique():,}")


# ── Breakdown by email_provider ───────────────────────────────────────────────

st.subheader("By enrichment provider")
st.caption("Which source produced the worst data. `email_provider` comes from sourced_contacts.")

by_provider = (
    bounces.groupby(bounces["email_provider"].fillna("(unknown)"), dropna=False)
    .agg(bounces=("lead_email", "count"),
         hard=("severity", lambda s: int((s == "hard").sum())),
         soft=("severity", lambda s: int((s == "soft").sum())),
         distinct_domains=("domain", "nunique"))
    .reset_index()
    .rename(columns={"email_provider": "provider"})
    .sort_values("bounces", ascending=False)
)
st.dataframe(by_provider, hide_index=True, use_container_width=True)


# ── Breakdown by bounce category ──────────────────────────────────────────────

st.subheader("By bounce category")

by_category = (
    bounces.groupby(["category", "severity"]).size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

c1, c2 = st.columns([2, 1])
with c1:
    fig = px.bar(by_category, x="category", y="count", color="severity",
                 color_discrete_map={"hard": "#dc2626", "soft": "#f59e0b", "unknown": "#9ca3af"},
                 title="Bounces by category")
    fig.update_layout(height=340, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.dataframe(by_category, hide_index=True, use_container_width=True)


# ── Breakdown by sender ───────────────────────────────────────────────────────

st.subheader("By sender (which BDR's domain is taking the hits)")
by_sender = (
    bounces.groupby(bounces["sender"].fillna("(unknown)"))
    .agg(bounces=("lead_email", "count"),
         hard=("severity", lambda s: int((s == "hard").sum())))
    .reset_index()
    .rename(columns={"sender": "sender"})
    .sort_values("bounces", ascending=False)
)
st.dataframe(by_sender, hide_index=True, use_container_width=True)


# ── Top failing domains ───────────────────────────────────────────────────────

st.subheader("Top failing domains")
by_domain = (
    bounces.groupby("domain")
    .agg(bounces=("lead_email", "count"),
         categories=("category", lambda s: ", ".join(sorted(set(s)))))
    .reset_index()
    .sort_values("bounces", ascending=False)
    .head(20)
)
st.dataframe(by_domain, hide_index=True, use_container_width=True)


# ── Recent bounces feed with parsed reasons ───────────────────────────────────

st.subheader("Recent bounces (latest 50)")
feed = bounces[[
    "received_at", "lead_email", "domain", "email_provider", "sender",
    "category", "severity", "smtp_code", "enhanced_code", "bounce_subject",
]].copy()
feed["received_at"] = pd.to_datetime(feed["received_at"]).dt.tz_convert("UTC").dt.strftime("%Y-%m-%d %H:%M")
st.dataframe(feed.head(50), hide_index=True, use_container_width=True)


# ── Raw text drill-down for unclassified ──────────────────────────────────────

unknowns = bounces[bounces["category"] == "unknown"]
if not unknowns.empty:
    st.subheader(f"⚠️ Unclassified bounces ({len(unknowns)})")
    st.caption(
        "Parser couldn't extract an SMTP code or matching phrase. Worth eyeballing"
        " these to find new patterns to add to bounce_parser.py."
    )
    st.dataframe(
        unknowns[["received_at", "lead_email", "bounce_subject", "bounce_from"]].head(20),
        hide_index=True, use_container_width=True,
    )
