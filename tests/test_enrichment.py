import json
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")

from pipelines.enrichment import build_prompt, build_batch_requests
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

SAMPLE_RESPONSE = {
    "response": {
        "industry": "Hospitality",
        "employees": "~7000",
        "email_crm_activity": "Runs a loyalty programme and sends promotional emails",
        "fit_score": 5,
        "reasoning": "Large hospitality group with 7000+ employees operating luxury hotels.",
        "has_wallet": False,
        "has_loyalty_program": True,
        "needs_cdp": True,
    }
}


async def _async_iter(items):
    for item in items:
        yield item


def _make_result(custom_id: str, response_dict: dict, result_type: str = "succeeded",
                 input_tokens: int = 500, output_tokens: int = 200):
    result = MagicMock()
    result.custom_id = custom_id
    result.result.type = result_type
    if result_type == "succeeded":
        result.result.message.content = [MagicMock(text=json.dumps(response_dict))]
        result.result.message.usage.input_tokens = input_tokens
        result.result.message.usage.output_tokens = output_tokens
    return result


# ── build_prompt ──────────────────────────────────────────────────────────────

def test_build_prompt_contains_company_and_domain():
    prompt = build_prompt("Acme Corp", "acme.com")
    assert "Acme Corp" in prompt
    assert "acme.com" in prompt


def test_build_prompt_contains_json_template():
    prompt = build_prompt("X", "x.com")
    assert '"fit_score"' in prompt
    assert '"has_wallet"' in prompt
    assert '"needs_cdp"' in prompt


# ── build_batch_requests ──────────────────────────────────────────────────────

def test_build_batch_requests_format():
    companies = [{"domain": "acme.com", "market": "UK", "company_name": "Acme"}]
    reqs = build_batch_requests(companies)
    assert len(reqs) == 1
    assert reqs[0]["custom_id"] == "acme_com_UK"
    assert reqs[0]["params"]["model"] == "claude-sonnet-4-6"
    assert reqs[0]["params"]["messages"][0]["role"] == "user"


def test_build_batch_requests_custom_id_separator():
    # custom_id must only use [a-zA-Z0-9_-] (Claude Batch API requirement)
    from pipelines.enrichment import _encode_custom_id, _decode_custom_id
    companies = [{"domain": "some.company.co.uk", "market": "UK", "company_name": "Co"}]
    reqs = build_batch_requests(companies)
    custom_id = reqs[0]["custom_id"]
    import re
    assert re.match(r'^[a-zA-Z0-9_-]+$', custom_id), f"Invalid custom_id: {custom_id}"
    domain, market = _decode_custom_id(custom_id)
    assert domain == "some.company.co.uk"
    assert market == "UK"


# ── POST /pipelines/enrich ────────────────────────────────────────────────────

def test_submit_endpoint_no_rows():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = MagicMock(data=[])

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}


def test_submit_endpoint_returns_batch_id():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[{"domain": "acme.com", "market": "UK", "company_name": "Acme"}]
    )

    mock_batch = MagicMock()
    mock_batch.id = "batch_abc123"

    mock_client = MagicMock()
    mock_client.messages.batches.create = AsyncMock(return_value=mock_batch)

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb), \
         patch("pipelines.enrichment._get_client", return_value=mock_client):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich")

    assert resp.status_code == 200
    body = resp.json()
    assert body["batch_ids"] == ["batch_abc123"]
    assert body["submitted"] == 1
    assert body["batches"] == 1


def test_submit_endpoint_writes_tracking_row():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[{"domain": "acme.com", "market": "UK", "company_name": "Acme"}]
    )

    mock_batch = MagicMock()
    mock_batch.id = "batch_abc123"

    mock_client = MagicMock()
    mock_client.messages.batches.create = AsyncMock(return_value=mock_batch)

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb), \
         patch("pipelines.enrichment._get_client", return_value=mock_client):
        from api.main import app
        tc = TestClient(app)
        tc.post("/pipelines/enrich")

    insert_calls = [
        call for call in mock_sb.table.return_value.insert.call_args_list
    ]
    assert len(insert_calls) == 1
    payload = insert_calls[0][0][0]
    assert payload["batch_id"] == "batch_abc123"
    assert payload["model"] == "claude-sonnet-4-6"
    assert payload["status"] == "pending"
    assert payload["companies_submitted"] == 1


def test_submit_endpoint_chunks_into_500():
    mock_sb = MagicMock()
    rows = [{"domain": f"co{i}.com", "market": "UK", "company_name": f"Co{i}"} for i in range(600)]
    mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = MagicMock(data=rows)

    mock_batch = MagicMock()
    mock_batch.id = "batch_xyz"

    mock_client = MagicMock()
    mock_client.messages.batches.create = AsyncMock(return_value=mock_batch)

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb), \
         patch("pipelines.enrichment._get_client", return_value=mock_client):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich")

    body = resp.json()
    assert body["submitted"] == 600
    assert body["batches"] == 2
    assert mock_client.messages.batches.create.call_count == 2
    first_call_requests = mock_client.messages.batches.create.call_args_list[0][1]["requests"]
    assert len(first_call_requests) == 500


# ── POST /pipelines/enrich/complete ──────────────────────────────────────────

def test_complete_endpoint_pending():
    mock_batch = MagicMock()
    mock_batch.processing_status = "in_progress"

    mock_client = MagicMock()
    mock_client.messages.batches.retrieve = AsyncMock(return_value=mock_batch)

    with patch("pipelines.enrichment._get_client", return_value=mock_client):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich/complete?batch_id=batch_xyz")

    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    assert resp.json()["batch_id"] == "batch_xyz"


def test_complete_endpoint_writes_results():
    mock_batch = MagicMock()
    mock_batch.processing_status = "ended"

    mock_result = _make_result("acme_com_UK", SAMPLE_RESPONSE)

    mock_client = MagicMock()
    mock_client.messages.batches.retrieve = AsyncMock(return_value=mock_batch)
    mock_client.messages.batches.results = AsyncMock(return_value=_async_iter([mock_result]))

    mock_sb = MagicMock()
    mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock()

    with patch("pipelines.enrichment._get_client", return_value=mock_client), \
         patch("pipelines.enrichment.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich/complete?batch_id=batch_xyz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["enriched"] == 1
    assert body["input_tokens"] == 500
    assert body["output_tokens"] == 200
    # $1.50/1M input + $7.50/1M output = 0.00075 + 0.0015 = 0.002250
    assert body["estimated_cost_usd"] == pytest.approx(0.002250, abs=1e-6)

    upserted = mock_sb.table.return_value.upsert.call_args[0][0]
    assert upserted[0]["domain"] == "acme.com"
    assert upserted[0]["market"] == "UK"
    assert upserted[0]["account_fit_score"] == 5
    assert upserted[0]["vertical"] == "Hospitality"
    assert upserted[0]["has_loyalty_program"] is True
    assert upserted[0]["needs_cdp"] is True

    update_payload = mock_sb.table.return_value.update.call_args[0][0]
    assert update_payload["status"] == "completed"
    assert update_payload["companies_enriched"] == 1
    assert update_payload["input_tokens"] == 500
    assert update_payload["output_tokens"] == 200
    assert update_payload["estimated_cost_usd"] == pytest.approx(0.002250, abs=1e-6)


def test_complete_endpoint_skips_failed_results():
    mock_batch = MagicMock()
    mock_batch.processing_status = "ended"

    failed_result = _make_result("bad_com_UK", {}, result_type="errored")
    good_result = _make_result("acme_com_UK", SAMPLE_RESPONSE)

    mock_client = MagicMock()
    mock_client.messages.batches.retrieve = AsyncMock(return_value=mock_batch)
    mock_client.messages.batches.results = AsyncMock(
        return_value=_async_iter([failed_result, good_result])
    )

    mock_sb = MagicMock()
    mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock()

    with patch("pipelines.enrichment._get_client", return_value=mock_client), \
         patch("pipelines.enrichment.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/enrich/complete?batch_id=batch_xyz")

    body = resp.json()
    assert body["status"] == "ok"
    assert body["enriched"] == 1
    upserted = mock_sb.table.return_value.upsert.call_args[0][0]
    assert upserted[0]["domain"] == "acme.com"


# ── POST /pipelines/prioritize ────────────────────────────────────────────────

def test_prioritize_endpoint_upserts_qualifying_rows():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.gte.return_value.execute.return_value = MagicMock(
        data=[
            {"domain": "acme.com", "market": "UK", "account_fit_score": 5,
             "company_name": "Acme", "vertical": "SaaS"},
            {"domain": "beta.com", "market": "UK", "account_fit_score": 3,
             "company_name": "Beta", "vertical": "Retail"},
        ]
    )

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/prioritize")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "prioritized": 2}
    mock_sb.table.return_value.upsert.assert_called_once()


def test_prioritize_endpoint_no_qualifying_rows():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.gte.return_value.execute.return_value = MagicMock(data=[])

    with patch("pipelines.enrichment.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/prioritize")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "prioritized": 0}
    mock_sb.table.return_value.upsert.assert_not_called()
