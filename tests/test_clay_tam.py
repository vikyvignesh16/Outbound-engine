import hmac
import hashlib
import json
import os
import pytest

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")
os.environ.setdefault("CLAY_WEBHOOK_SECRET", "test-secret")

WHITBREAD_ROW = {
    "Name": "Whitbread",
    "Type": "Public Company",
    "Size": "10,001+ employees",
    "Location": "Houghton Regis, Dunstable",
    "Country": "United Kingdom",
    "LinkedIn URL": "https://www.linkedin.com/company/whitbread",
    "Domain": "whitbreadcareers.com",
    "Brevo Company ID": "",
    "Nb Open Deals": None,
    "Deal Lost Date": None,
    "Primary Industry": "Hospitality",
    "ID": "https://www.linkedin.com/company/whitbread-United Kingdom",
}


def _make_signature(body: bytes, secret: str = "test-secret") -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture()
def client():
    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = MagicMock()

    mock_table = MagicMock()
    mock_table.upsert.return_value = mock_upsert

    mock_supabase = MagicMock()
    mock_supabase.table.return_value = mock_table

    with patch("webhooks.clay_tam.get_supabase", return_value=mock_supabase):
        from api.main import app
        yield TestClient(app), mock_supabase


def test_valid_payload_returns_ok(client):
    tc, mock_sb = client
    body = json.dumps([WHITBREAD_ROW]).encode()
    sig = _make_signature(body)

    resp = tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "accepted": 1}
    mock_sb.table.assert_called_once_with("sourced_tam_v2")


def test_invalid_signature_returns_401(client):
    tc, _ = client
    body = json.dumps([WHITBREAD_ROW]).encode()

    resp = tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": "bad-sig", "content-type": "application/json"},
    )

    assert resp.status_code == 401


def test_missing_domain_returns_422(client):
    tc, _ = client
    row = {k: v for k, v in WHITBREAD_ROW.items() if k != "Domain"}
    body = json.dumps([row]).encode()
    sig = _make_signature(body)

    resp = tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    assert resp.status_code == 422


def test_country_normalised_to_market_code(client):
    tc, mock_sb = client
    body = json.dumps([WHITBREAD_ROW]).encode()
    sig = _make_signature(body)

    tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    upserted_rows = mock_sb.table().upsert.call_args[0][0]
    assert upserted_rows[0]["market"] == "UK"


def test_unknown_country_stored_as_is(client):
    tc, mock_sb = client
    row = {**WHITBREAD_ROW, "Country": "Narnia"}
    body = json.dumps([row]).encode()
    sig = _make_signature(body)

    tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    upserted_rows = mock_sb.table().upsert.call_args[0][0]
    assert upserted_rows[0]["market"] == "Narnia"


def test_empty_brevo_company_id_coerced_to_none(client):
    tc, mock_sb = client
    body = json.dumps([WHITBREAD_ROW]).encode()
    sig = _make_signature(body)

    tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    upserted_rows = mock_sb.table().upsert.call_args[0][0]
    assert upserted_rows[0]["brevo_company_id"] is None


def test_batch_of_multiple_rows(client):
    tc, mock_sb = client
    row_fr = {**WHITBREAD_ROW, "Domain": "company.fr", "Country": "France"}
    body = json.dumps([WHITBREAD_ROW, row_fr]).encode()
    sig = _make_signature(body)

    resp = tc.post(
        "/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
    )

    assert resp.json()["accepted"] == 2
    upserted_rows = mock_sb.table().upsert.call_args[0][0]
    markets = {r["market"] for r in upserted_rows}
    assert markets == {"UK", "FR"}
