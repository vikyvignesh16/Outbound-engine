import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")
os.environ.setdefault("TECHNOGRAPHIC_API_KEY", "test-api-key")

from pipelines.qualification import compute_esp_score, get_primary_esp, run_step2
from fastapi.testclient import TestClient


# ── compute_esp_score ─────────────────────────────────────────────────────────

def test_compute_esp_score_mailchimp():
    assert compute_esp_score([{"name": "Mailchimp"}]) == 100

def test_compute_esp_score_activecampaign():
    assert compute_esp_score([{"name": "ActiveCampaign"}]) == 100

def test_compute_esp_score_campaign_monitor():
    assert compute_esp_score([{"name": "Campaign Monitor"}]) == 100

def test_compute_esp_score_sendgrid():
    assert compute_esp_score([{"name": "SendGrid"}]) == 75

def test_compute_esp_score_mailgun():
    assert compute_esp_score([{"name": "Mailgun"}]) == 75

def test_compute_esp_score_hubspot():
    assert compute_esp_score([{"name": "HubSpot"}]) == 25

def test_compute_esp_score_klaviyo():
    assert compute_esp_score([{"name": "Klaviyo"}]) == 25

def test_compute_esp_score_salesforce():
    assert compute_esp_score([{"name": "Salesforce Marketing Cloud"}]) == 0

def test_compute_esp_score_marketo():
    assert compute_esp_score([{"name": "Marketo"}]) == 0

def test_compute_esp_score_unknown_name():
    assert compute_esp_score([{"name": "SomeTotallyUnknownESP"}]) == 50

def test_compute_esp_score_empty_list():
    assert compute_esp_score([]) == 0

def test_compute_esp_score_multiple_takes_highest():
    esps = [{"name": "HubSpot"}, {"name": "Mailchimp"}]
    assert compute_esp_score(esps) == 100

def test_compute_esp_score_multiple_all_low():
    esps = [{"name": "Salesforce Marketing Cloud"}, {"name": "Marketo"}]
    assert compute_esp_score(esps) == 0


# ── get_primary_esp ───────────────────────────────────────────────────────────

def test_get_primary_esp_returns_highest_scorer():
    esps = [{"name": "HubSpot"}, {"name": "Mailchimp"}, {"name": "SendGrid"}]
    assert get_primary_esp(esps) == "Mailchimp"

def test_get_primary_esp_single():
    assert get_primary_esp([{"name": "SendGrid"}]) == "SendGrid"

def test_get_primary_esp_empty():
    assert get_primary_esp([]) is None


# ── POST /pipelines/qualify endpoint ─────────────────────────────────────────

MOCK_TECHSTACK_RESPONSE = {
    "domain": "acme.com",
    "tech_score": 10,
    "esp": [{"name": "Mailchimp", "confidence": "high", "source": "spf"}],
    "crm": [], "cms": [], "ecommerce": [],
}


@pytest.fixture()
def client():
    mock_select = MagicMock()
    mock_select.is_.return_value.execute.return_value = MagicMock(
        data=[{"domain": "acme.com", "market": "UK"}]
    )

    mock_update = MagicMock()
    mock_update.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value = mock_select
    mock_sb.table.return_value.update.return_value = mock_update

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb), \
         patch("pipelines.qualification.get_techstack", new=AsyncMock(return_value=MOCK_TECHSTACK_RESPONSE)):
        from api.main import app
        yield TestClient(app), mock_sb


def test_qualify_endpoint_returns_ok(client):
    tc, _ = client
    resp = tc.post("/pipelines/qualify")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["processed"] == 1


def test_qualify_endpoint_writes_correct_esp(client):
    tc, mock_sb = client
    tc.post("/pipelines/qualify")
    call_args = mock_sb.table.return_value.update.call_args[0][0]
    assert call_args["esp_detected"] == "Mailchimp"
    assert call_args["esp_score"] == 100


def test_qualify_endpoint_no_unqualified_rows():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = MagicMock(data=[])

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        resp = tc.post("/pipelines/qualify")
    assert resp.json() == {"status": "ok", "processed": 0}
