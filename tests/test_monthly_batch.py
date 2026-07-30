import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")

from fastapi.testclient import TestClient

PRIORITY_ROWS = [
    {"domain": "acme.com",  "market": "UK", "company_name": "Acme",  "account_fit_score": 5, "vertical": "SaaS"},
    {"domain": "beta.com",  "market": "UK", "company_name": "Beta",  "account_fit_score": 4, "vertical": "Retail"},
    {"domain": "gamma.com", "market": "UK", "company_name": "Gamma", "account_fit_score": 3, "vertical": "Fintech"},
]


def _chainable(data):
    """Mimics fetch_all's real call pattern: table().select(...).range(...)
    .<filters>.<orders>.execute(). Every chain method returns the SAME node
    so it works regardless of how many filters/orders are applied — except
    .range(), which must actually slice by offset or fetch_all's pagination
    loop (which keeps requesting .range(offset, offset+999) until a short
    page comes back) never terminates and spins forever on >1000-row data."""
    def make_node(rows):
        node = MagicMock()
        for method in ("select", "eq", "is_", "in_", "neq", "limit", "order"):
            getattr(node, method).return_value = node
        node.range.side_effect = lambda start, end: make_node(rows[start:end + 1])
        node.execute.return_value = MagicMock(data=rows)
        return node
    return make_node(data)


def _make_mock(campaign_rows=None, priority_rows=None):
    if campaign_rows is None:
        campaign_rows = []
    if priority_rows is None:
        priority_rows = PRIORITY_ROWS

    mock_sb = MagicMock()

    campaign_tbl = _chainable(campaign_rows)
    campaign_tbl.insert.return_value.execute.return_value = MagicMock()

    priority_tbl = _chainable(priority_rows)

    tables = {"campaign_batches": campaign_tbl, "priority_tam": priority_tbl}
    mock_sb.table.side_effect = lambda name: tables.get(name, MagicMock())
    return mock_sb, campaign_tbl, priority_tbl


def _patch_supabase(mock_sb):
    """fetch_all() calls db.client.get_supabase() directly (not the copy imported
    into pipelines.monthly_batch), so both need patching to the same mock for
    fetch_all's internal reads and monthly_batch's own inserts/updates to see
    the same table data."""
    return (
        patch("pipelines.monthly_batch.get_supabase", return_value=mock_sb),
        patch("db.client.get_supabase", return_value=mock_sb),
    )


def test_monthly_batch_selects_uncontacted():
    mock_sb, campaign_tbl, _ = _make_mock()
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["selected"] == 3
    assert body["group_counts"]["UKI"] == 3
    assert body["group_counts"]["DACH"] == 0
    assert body["batch_numbers"]["UKI"] == 1


def test_monthly_batch_skips_already_contacted():
    already = [{"domain": "acme.com", "market": "UK", "company_name": "Acme", "batch_number": 1}]
    mock_sb, campaign_tbl, _ = _make_mock(campaign_rows=already)
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["selected"] == 2
    assert body["group_counts"]["UKI"] == 2
    assert body["batch_numbers"]["UKI"] == 2
    inserted = campaign_tbl.insert.call_args[0][0]
    domains = [r["domain"] for r in inserted]
    assert "acme.com" not in domains


def test_monthly_batch_respects_500_per_market_limit():
    uk_rows = [
        {"domain": f"uk{i}.com", "market": "UK", "company_name": f"UK{i}",
         "account_fit_score": 3, "vertical": "SaaS"}
        for i in range(600)
    ]
    dach_rows = [
        {"domain": f"de{i}.com", "market": "DE", "company_name": f"DE{i}",
         "account_fit_score": 3, "vertical": "SaaS"}
        for i in range(600)
    ]
    mock_sb, campaign_tbl, _ = _make_mock(priority_rows=uk_rows + dach_rows)
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["selected"] == 1000
    assert body["group_counts"]["UKI"] == 500
    assert body["group_counts"]["DACH"] == 500
    total_inserted = sum(
        len(call[0][0]) for call in campaign_tbl.insert.call_args_list
    )
    assert total_inserted == 1000


def test_monthly_batch_no_candidates():
    mock_sb, campaign_tbl, _ = _make_mock(priority_rows=[])
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["status"] == "ok"
    assert body["selected"] == 0
    campaign_tbl.insert.assert_not_called()


def test_monthly_batch_correct_batch_month():
    from datetime import date
    mock_sb, campaign_tbl, _ = _make_mock()
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    expected_month = date.today().replace(day=1).isoformat()
    assert resp.json()["batch_month"] == expected_month
    inserted = campaign_tbl.insert.call_args[0][0]
    assert all(r["batch_month"] == expected_month for r in inserted)


def test_monthly_batch_numbering_is_independent_per_group():
    """The core behavior this session's work is about: an existing UKI batch
    (already at #3) must NOT bump DACH's first-ever batch past #1 — each
    market group keeps its own sequence."""
    existing = [
        {"domain": "old.com", "market": "UK", "company_name": "Old", "batch_number": 3},
    ]
    priority_rows = PRIORITY_ROWS + [
        {"domain": "muc.de", "market": "DE", "company_name": "Munich Co", "account_fit_score": 4, "vertical": "SaaS"},
    ]
    mock_sb, campaign_tbl, _ = _make_mock(campaign_rows=existing, priority_rows=priority_rows)
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch")
    body = resp.json()
    assert body["batch_numbers"]["UKI"] == 4   # UKI's 4th batch (already had #3)
    assert body["batch_numbers"]["DACH"] == 1  # DACH's 1st batch, unaffected by UKI's count
    inserted = campaign_tbl.insert.call_args[0][0]
    uk_rows = [r for r in inserted if r["market"] == "UK"]
    de_rows = [r for r in inserted if r["market"] == "DE"]
    assert all(r["batch_number"] == 4 for r in uk_rows)
    assert all(r["batch_number"] == 1 for r in de_rows)


# ── POST /pipelines/monthly-batch/push ───────────────────────────────────────

DACH_BATCH_1_ROWS = [
    {"id": "1", "domain": "berlin.de", "market": "DE", "company_name": "Berlin", "account_fit_score": 4, "vertical": "Retail", "batch_month": "2026-07-01"},
    {"id": "2", "domain": "vienna.at", "market": "AT", "company_name": "Vienna", "account_fit_score": 4, "vertical": "Retail", "batch_month": "2026-07-01"},
    {"id": "3", "domain": "zurich.ch", "market": "CH", "company_name": "Zurich", "account_fit_score": 3, "vertical": "Fintech", "batch_month": "2026-07-01"},
]


def _make_push_mock(rows):
    mock_sb = MagicMock()
    campaign_tbl = _chainable(rows)
    campaign_tbl.update.return_value.in_.return_value.execute.return_value = MagicMock()
    mock_sb.table.return_value = campaign_tbl
    return mock_sb, campaign_tbl


def test_push_groups_dach_into_single_webhook():
    mock_sb, _ = _make_push_mock(DACH_BATCH_1_ROWS)
    mock_response = MagicMock(status_code=200)
    mock_response.raise_for_status = MagicMock()

    mock_post = AsyncMock(return_value=mock_response)
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2, \
         patch.dict(os.environ, {"CLAY_WEBHOOK_UK": "https://clay.run/uk", "CLAY_WEBHOOK_DACH": "https://clay.run/dach"}), \
         patch("httpx.AsyncClient.post", mock_post):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?market_group=DACH&batch_number=1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["market_group"] == "DACH"
    # UK isn't part of the DACH group's push at all — group isolation is the point.
    assert "CLAY_WEBHOOK_UK" not in body["webhooks"]
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["status"] == "ok"
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["companies"] == 3  # DE + AT + CH
    assert mock_post.call_count == 3


def test_push_skips_webhook_not_configured():
    mock_sb, _ = _make_push_mock(DACH_BATCH_1_ROWS)
    mock_response = MagicMock(status_code=200)
    mock_response.raise_for_status = MagicMock()

    os.environ.pop("CLAY_WEBHOOK_DACH", None)
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2, \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?market_group=DACH&batch_number=1")

    body = resp.json()
    assert body["webhooks"]["CLAY_WEBHOOK_DACH"]["status"] == "skipped"


def test_push_already_pushed_for_unknown_batch():
    mock_sb, _ = _make_push_mock([])
    p1, p2 = _patch_supabase(mock_sb)
    with p1, p2:
        from api.main import app
        resp = TestClient(app).post("/pipelines/monthly-batch/push?market_group=DACH&batch_number=99")
    assert resp.status_code == 200
    body = resp.json()
    assert body["already_pushed"] is True
    assert body["webhooks"] == {}
