import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")

from fastapi.testclient import TestClient

PRIORITY_ROWS = [
    {"domain": "acme.com",   "market": "UK", "company_name": "Acme",  "account_fit_score": 5, "vertical": "SaaS"},
    {"domain": "beta.com",   "market": "UK", "company_name": "Beta",  "account_fit_score": 4, "vertical": "Retail"},
    {"domain": "gamma.com",  "market": "UK", "company_name": "Gamma", "account_fit_score": 3, "vertical": "Fintech"},
]


def _make_mock(campaign_rows=None, priority_rows=None):
    if campaign_rows is None:
        campaign_rows = []
    if priority_rows is None:
        priority_rows = PRIORITY_ROWS

    mock_sb = MagicMock()

    campaign_tbl = MagicMock()
    campaign_tbl.select.return_value.execute.return_value = MagicMock(data=campaign_rows)
    campaign_tbl.insert.return_value.execute.return_value = MagicMock()

    priority_tbl = MagicMock()
    priority_tbl.select.return_value.order.return_value.order.return_value.execute.return_value = MagicMock(data=priority_rows)

    tables = {"campaign_batches": campaign_tbl, "priority_tam": priority_tbl}
    mock_sb.table.side_effect = lambda name: tables.get(name, MagicMock())
    return mock_sb, campaign_tbl, priority_tbl


def test_monthly_batch_selects_uncontacted():
    mock_sb, campaign_tbl, _ = _make_mock()
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["selected"] == 3
    assert body["batch_number"] == 1


def test_monthly_batch_skips_already_contacted():
    already = [{"domain": "acme.com", "market": "UK", "batch_number": 1}]
    mock_sb, campaign_tbl, _ = _make_mock(campaign_rows=already)
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["selected"] == 2
    assert body["batch_number"] == 2
    inserted = campaign_tbl.insert.call_args[0][0]
    domains = [r["domain"] for r in inserted]
    assert "acme.com" not in domains


def test_monthly_batch_respects_1000_limit():
    big_list = [
        {"domain": f"co{i}.com", "market": "UK", "company_name": f"Co{i}",
         "account_fit_score": 3, "vertical": "SaaS"}
        for i in range(1200)
    ]
    mock_sb, campaign_tbl, _ = _make_mock(priority_rows=big_list)
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    assert resp.json()["selected"] == 1000
    total_inserted = sum(
        len(call[0][0]) for call in campaign_tbl.insert.call_args_list
    )
    assert total_inserted == 1000


def test_monthly_batch_no_candidates():
    mock_sb, campaign_tbl, _ = _make_mock(priority_rows=[])
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["status"] == "ok"
    assert body["selected"] == 0
    campaign_tbl.insert.assert_not_called()


def test_monthly_batch_correct_batch_month():
    from datetime import date
    mock_sb, campaign_tbl, _ = _make_mock()
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    expected_month = date.today().replace(day=1).isoformat()
    assert resp.json()["batch_month"] == expected_month
    inserted = campaign_tbl.insert.call_args[0][0]
    assert all(r["batch_month"] == expected_month for r in inserted)


def test_monthly_batch_increments_batch_number():
    existing = [
        {"domain": "old.com", "market": "UK", "batch_number": 3},
    ]
    mock_sb, campaign_tbl, _ = _make_mock(campaign_rows=existing)
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    assert resp.json()["batch_number"] == 4
    inserted = campaign_tbl.insert.call_args[0][0]
    assert all(r["batch_number"] == 4 for r in inserted)


# ── POST /pipelines/monthly-batch/push ───────────────────────────────────────

BATCH_1_ROWS = [
    {"domain": "acme.com",    "market": "UK", "company_name": "Acme",    "account_fit_score": 5, "vertical": "SaaS",   "batch_month": "2026-05-01"},
    {"domain": "berlin.de",   "market": "DE", "company_name": "Berlin",  "account_fit_score": 4, "vertical": "Retail", "batch_month": "2026-05-01"},
    {"domain": "vienna.at",   "market": "AT", "company_name": "Vienna",  "account_fit_score": 4, "vertical": "Retail", "batch_month": "2026-05-01"},
    {"domain": "zurich.ch",   "market": "CH", "company_name": "Zurich",  "account_fit_score": 3, "vertical": "Fintech","batch_month": "2026-05-01"},
]


def _make_push_mock(rows=None):
    rows = rows if rows is not None else BATCH_1_ROWS
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=rows)
    return mock_sb


def test_push_groups_dach_into_single_webhook():
    mock_sb = _make_push_mock()
    mock_response = MagicMock(status_code=200)
    mock_response.raise_for_status = MagicMock()

    mock_post = AsyncMock(return_value=mock_response)
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb), \
         patch.dict(os.environ, {"CLAY_WEBHOOK_UK": "https://clay.run/uk", "CLAY_WEBHOOK_DACH": "https://clay.run/dach"}), \
         patch("httpx.AsyncClient.post", mock_post):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?batch_number=1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["webhooks"]["CLAY_WEBHOOK_UK"]["status"] == "ok"
    assert body["webhooks"]["CLAY_WEBHOOK_UK"]["companies"] == 1
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["status"] == "ok"
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["companies"] == 3  # DE + AT + CH
    # Each company is a separate POST — 4 total (1 UK + 3 DACH)
    assert mock_post.call_count == 4


def test_push_skips_webhook_not_configured():
    mock_sb = _make_push_mock()
    mock_response = MagicMock(status_code=200)
    mock_response.raise_for_status = MagicMock()

    os.environ.pop("CLAY_WEBHOOK_DACH", None)
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb), \
         patch.dict(os.environ, {"CLAY_WEBHOOK_UK": "https://clay.run/uk"}), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?batch_number=1")

    body = resp.json()
    assert body["webhooks"]["CLAY_WEBHOOK_UK"]["status"] == "ok"
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["status"] == "skipped"


def test_push_returns_404_for_unknown_batch():
    mock_sb = _make_push_mock(rows=[])
    with patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?batch_number=99")
    assert resp.status_code == 404
