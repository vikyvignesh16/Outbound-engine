"""Campaign Performance — Lemlist engagement metrics, bot-filtered.

Uses lemlist_activities.is_bot (migration 041) to filter scanner clicks
out of the real engagement numbers.
"""
import streamlit as st
import plotly.express as px

from lib.db import query_df

if not st.session_state.get("authed"):
    st.warning("Please sign in via the home page.")
    st.stop()

st.set_page_config(page_title="Campaign Performance | ABM V2", layout="wide")
st.title("📨 Campaign Performance")
st.caption("Lemlist engagement, with bot events excluded by default.")


# ── Campaign picker ───────────────────────────────────────────────────────────

campaigns = query_df("""
SELECT campaign_id,
       campaign_name,
       COUNT(*) AS events,
       MIN(received_at) AS first_event,
       MAX(received_at) AS last_event
FROM lemlist_activities
WHERE campaign_id IS NOT NULL AND campaign_name IS NOT NULL
GROUP BY campaign_id, campaign_name
HAVING COUNT(*) >= 5
ORDER BY MAX(received_at) DESC
""")

if campaigns.empty:
    st.info("No campaign data yet.")
    st.stop()

selected = st.selectbox(
    "Campaign",
    options=campaigns["campaign_id"].tolist(),
    format_func=lambda cid: f"{campaigns.set_index('campaign_id').loc[cid, 'campaign_name']}  ({campaigns.set_index('campaign_id').loc[cid, 'events']:,} events)",
)

camp_row = campaigns[campaigns["campaign_id"] == selected].iloc[0]
st.markdown(f"**{camp_row['campaign_name']}** &nbsp;·&nbsp; `{selected}`")
st.caption(f"First event: {camp_row['first_event']} &nbsp;·&nbsp; Last event: {camp_row['last_event']}")


# ── Headline rates ────────────────────────────────────────────────────────────

st.subheader("Engagement rates (bot-filtered)")

agg = query_df("""
SELECT
  COUNT(DISTINCT lead_email) FILTER (WHERE event_type = 'emailsSent')                                      AS unique_sent,
  COUNT(DISTINCT lead_email) FILTER (WHERE event_type = 'emailsOpened'  AND is_bot IS NOT TRUE)            AS unique_opened,
  COUNT(DISTINCT lead_email) FILTER (WHERE event_type = 'emailsClicked' AND is_bot IS NOT TRUE)            AS unique_clicked,
  COUNT(DISTINCT lead_email) FILTER (WHERE event_type = 'emailsReplied')                                   AS unique_replied,
  COUNT(DISTINCT lead_email) FILTER (WHERE event_type = 'emailsBounced')                                   AS unique_bounced,
  COUNT(*) FILTER (WHERE event_type = 'emailsClicked' AND is_bot IS TRUE)                                  AS bot_click_events,
  COUNT(*) FILTER (WHERE event_type = 'emailsClicked' AND is_bot IS NOT TRUE)                              AS human_click_events
FROM lemlist_activities
WHERE campaign_id = %s
""", (selected,))

if agg.empty or agg.iloc[0]["unique_sent"] == 0:
    st.info("No emailsSent events yet for this campaign.")
else:
    a = agg.iloc[0]
    sent = max(1, a["unique_sent"])
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sent",     f"{a['unique_sent']:,}")
    c2.metric("Opened",   f"{a['unique_opened']:,}",   f"{a['unique_opened']  / sent * 100:.1f}%")
    c3.metric("Clicked",  f"{a['unique_clicked']:,}",  f"{a['unique_clicked'] / sent * 100:.1f}%")
    c4.metric("Replied",  f"{a['unique_replied']:,}",  f"{a['unique_replied'] / sent * 100:.1f}%")
    c5.metric("Bounced",  f"{a['unique_bounced']:,}",  f"{a['unique_bounced'] / sent * 100:.1f}%")
    st.caption(
        f"Bot filtering caught {a['bot_click_events']:,} bot-click events out of "
        f"{a['bot_click_events'] + a['human_click_events']:,} total click events "
        f"({100 * a['bot_click_events'] / max(1, a['bot_click_events'] + a['human_click_events']):.1f}% bot)."
    )


# ── Daily timeline ────────────────────────────────────────────────────────────

st.subheader("Daily activity")

daily = query_df("""
SELECT DATE_TRUNC('day', received_at AT TIME ZONE 'UTC')::date AS day,
       COUNT(*) FILTER (WHERE event_type='emailsSent')                                  AS sent,
       COUNT(*) FILTER (WHERE event_type='emailsOpened'  AND is_bot IS NOT TRUE)        AS opened,
       COUNT(*) FILTER (WHERE event_type='emailsClicked' AND is_bot IS NOT TRUE)        AS clicked,
       COUNT(*) FILTER (WHERE event_type='emailsReplied')                               AS replied,
       COUNT(*) FILTER (WHERE event_type='emailsBounced')                               AS bounced,
       COUNT(*) FILTER (WHERE event_type LIKE 'linkedin%%')                             AS linkedin
FROM lemlist_activities
WHERE campaign_id = %s
GROUP BY day ORDER BY day
""", (selected,))
if not daily.empty:
    fig = px.line(daily, x="day", y=["sent","opened","clicked","replied","bounced","linkedin"],
                  title="Events per day (bot-filtered for opened/clicked)")
    fig.update_layout(height=380, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(daily, hide_index=True, use_container_width=True)


# ── Event type breakdown ──────────────────────────────────────────────────────

st.subheader("Event type breakdown")

ev = query_df("""
SELECT event_type,
       COUNT(*) AS events,
       COUNT(*) FILTER (WHERE is_bot IS TRUE) AS bot_events,
       COUNT(*) FILTER (WHERE is_bot IS NOT TRUE) AS human_events,
       COUNT(DISTINCT lead_email) AS unique_leads
FROM lemlist_activities
WHERE campaign_id = %s
GROUP BY event_type
ORDER BY events DESC
""", (selected,))
st.dataframe(ev, hide_index=True, use_container_width=True)


# ── Top engaged accounts ──────────────────────────────────────────────────────

st.subheader("Top engaged domains (humans only)")

top = query_df("""
SELECT domain,
       COUNT(*) FILTER (WHERE event_type='emailsOpened'  AND is_bot IS NOT TRUE) AS human_opens,
       COUNT(*) FILTER (WHERE event_type='emailsClicked' AND is_bot IS NOT TRUE) AS human_clicks,
       COUNT(*) FILTER (WHERE event_type='emailsReplied')                        AS replies,
       COUNT(*) FILTER (WHERE event_type LIKE 'linkedin%%' AND event_type NOT LIKE '%%Failed')
         AS linkedin_actions
FROM lemlist_activities
WHERE campaign_id = %s AND domain IS NOT NULL
GROUP BY domain
ORDER BY replies DESC, human_clicks DESC, human_opens DESC
LIMIT 30
""", (selected,))
st.dataframe(top, hide_index=True, use_container_width=True)
