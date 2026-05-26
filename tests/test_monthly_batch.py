import os
import pytest
from unittest.mock import MagicMock, patch

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
