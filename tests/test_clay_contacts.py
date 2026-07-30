import os
import pytest

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")
os.environ.setdefault("CLAY_CONTACTS_WEBHOOK_SECRET", "test-secret")

CONTACT = {
    "domain": "onestop.co.uk",
    "linkedin_url": "https://www.linkedin.com/in/Jamie-Voss/",
    "market": "UK",
    "company_name": "One Stop Retail Group",
    "email": "jamie@onestop.co.uk",
    "first_name": "Jamie",
    "last_name": "Voss",
    "job_title": "Head of Marketing",
    "relevance_score": 5,
    "relevance_reasoning": "CMO-equivalent title",
    "location": "London",
    "country": "United Kingdom",
}

HEADERS = {"x-clay-contacts-secret": "test-secret"}


@pytest.fixture()
def client():
    mock_campaign_batches_query = MagicMock()
    mock_campaign_batches_query.execute.return_value = MagicMock(data=[{"batch_number": 3}])

    mock_campaign_batches_table = MagicMock()
    mock_campaign_batches_table.select.return_value.eq.return_value.eq.return_value.limit.return_value = (
        mock_campaign_batches_query
    )

    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = MagicMock()

    mock_sourced_contacts_table = MagicMock()
    mock_sourced_contacts_table.upsert.return_value = mock_upsert

    def _table(name):
        if name == "campaign_batches":
            return mock_campaign_batches_table
        if name == "sourced_contacts":
            return mock_sourced_contacts_table
        raise AssertionError(f"unexpected table: {name}")

    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = _table

    with patch("webhooks.clay_contacts.get_supabase", return_value=mock_supabase):
        from api.main import app
        yield TestClient(app), mock_sourced_contacts_table


def test_valid_payload_returns_ok(client):
    tc, mock_table = client
    resp = tc.post("/webhooks/clay/contacts", json=CONTACT, headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "inserted": 1}
    mock_table.upsert.assert_called_once()
    kwargs = mock_table.upsert.call_args
    assert kwargs.kwargs["on_conflict"] == "linkedin_url"


def test_linkedin_url_normalised_before_upsert(client):
    tc, mock_table = client
    tc.post("/webhooks/clay/contacts", json=CONTACT, headers=HEADERS)

    row = mock_table.upsert.call_args[0][0]
    assert row["linkedin_url"] == "linkedin.com/in/jamie-voss"


def test_batch_number_resolved_from_campaign_batches(client):
    tc, mock_table = client
    tc.post("/webhooks/clay/contacts", json=CONTACT, headers=HEADERS)

    row = mock_table.upsert.call_args[0][0]
    assert row["batch_number"] == 3


def test_explicit_batch_number_takes_precedence(client):
    tc, mock_table = client
    contact = {**CONTACT, "batch_number": 9}
    tc.post("/webhooks/clay/contacts", json=contact, headers=HEADERS)

    row = mock_table.upsert.call_args[0][0]
    assert row["batch_number"] == 9


def test_location_and_country_stored_in_raw(client):
    tc, mock_table = client
    tc.post("/webhooks/clay/contacts", json=CONTACT, headers=HEADERS)

    row = mock_table.upsert.call_args[0][0]
    assert row["raw"]["location"] == "London"
    assert row["raw"]["country"] == "United Kingdom"
    assert row["raw"]["clay_full_payload"] == CONTACT


def test_missing_secret_returns_401(client):
    tc, _ = client
    resp = tc.post("/webhooks/clay/contacts", json=CONTACT)
    assert resp.status_code == 401


def test_invalid_secret_returns_401(client):
    tc, _ = client
    resp = tc.post(
        "/webhooks/clay/contacts", json=CONTACT, headers={"x-clay-contacts-secret": "wrong"}
    )
    assert resp.status_code == 401


def test_missing_domain_returns_422(client):
    tc, _ = client
    contact = {k: v for k, v in CONTACT.items() if k != "domain"}
    resp = tc.post("/webhooks/clay/contacts", json=contact, headers=HEADERS)
    assert resp.status_code == 422


def test_missing_market_returns_422(client):
    tc, _ = client
    contact = {k: v for k, v in CONTACT.items() if k != "market"}
    resp = tc.post("/webhooks/clay/contacts", json=contact, headers=HEADERS)
    assert resp.status_code == 422


def test_missing_linkedin_url_returns_422(client):
    tc, _ = client
    contact = {k: v for k, v in CONTACT.items() if k != "linkedin_url"}
    resp = tc.post("/webhooks/clay/contacts", json=contact, headers=HEADERS)
    assert resp.status_code == 422


def test_blank_linkedin_url_returns_422(client):
    tc, _ = client
    contact = {**CONTACT, "linkedin_url": "   "}
    resp = tc.post("/webhooks/clay/contacts", json=contact, headers=HEADERS)
    assert resp.status_code == 422
