# Brevo ABM V2 — Streamlit Dashboard

Operations dashboard for the ABM V2 pipeline. Reads Supabase directly,
deployed on Streamlit Community Cloud (free tier).

## Layout

```
dashboard/
├── streamlit_app.py        # home + password gate
├── pages/
│   ├── 1_Pipeline_Funnel.py
│   ├── 2_Campaign_Performance.py
│   └── 3_Operational_Health.py
├── lib/db.py               # cached Postgres connection helpers
├── .streamlit/config.toml  # theme
├── .streamlit/secrets.toml.example
└── requirements.txt
```

## Local dev

1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`,
   fill in `SUPABASE_DB_URL` and `APP_PASSWORD`.
2. `cd dashboard && pip install -r requirements.txt`
3. `streamlit run streamlit_app.py`
4. Open http://localhost:8501

## Deploying to Streamlit Community Cloud

One-time setup (~10 min):

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with the
   GitHub account that has access to the `brevo-outbound-engine` repo.
2. Click **New app** → pick the repo.
3. Fields:
   - **Branch**: `main`
   - **Main file path**: `dashboard/streamlit_app.py`
   - **Python version**: 3.11 (or default)
4. Click **Advanced settings** → **Secrets**. Paste:
   ```toml
   SUPABASE_DB_URL = "postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres"
   APP_PASSWORD = "<pick-a-strong-password>"
   ```
5. Click **Deploy**. First build takes ~2-3 min.
6. Once live, the URL is `https://<some-name>.streamlit.app` — share with the team.

### Updates

Push to `main`; Streamlit Cloud auto-redeploys within ~30 seconds. No CI/CD
to configure.

### Auth

The home page has a simple password gate using `APP_PASSWORD` from secrets.
For production, consider upgrading to Streamlit's Google SSO (paid) or
adding Supabase Auth in front of the app.

## Performance notes

- Single Postgres connection per Streamlit session, cached via
  `@st.cache_resource`.
- Each query is cached 5 minutes (`@st.cache_data(ttl=300)`), so refreshing
  a page hits Supabase only if the cache has expired.
- For very large queries, add `LIMIT` or aggregate in SQL before fetching.

## Adding a new page

Create `dashboard/pages/N_Page_Name.py`. Streamlit auto-discovers it in the
sidebar (sorted by numeric prefix). Copy the auth-check + page_config
pattern from the existing pages.
