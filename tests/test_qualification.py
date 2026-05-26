import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test")
os.environ.setdefault("TECHNOGRAPHIC_API_KEY", "test-api-key")
os.environ.setdefault("BREVO_CRM_API_KEY", "test-brevo-key")

from pipelines.qualification import compute_esp_score, get_primary_esp, apply_rules
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


# ── apply_rules ───────────────────────────────────────────────────────────────

def test_apply_rules_new_prospect():
    row = {"brevo_company_id": None, "planhat_id": None, "open_deals": 0, "deal_lost_date": None}
    qualifies, reason = apply_rules(row)
    assert qualifies is True
    assert reason is None

def test_apply_rules_existing_customer():
    row = {"brevo_company_id": "abc123", "planhat_id": "ph_456", "open_deals": 0, "deal_lost_date": None}
    qualifies, reason = apply_rules(row)
    assert qualifies is False
    assert reason == "existing_customer"

def test_apply_rules_open_deal_no_lost_date():
    row = {"brevo_company_id": "abc123", "planhat_id": None, "open_deals": 2, "deal_lost_date": None}
    qualifies, reason = apply_rules(row)
    assert qualifies is False
    assert reason == "open_deal_exists"

def test_apply_rules_open_deal_with_lost_date():
    # open deal count is non-zero but there is a lost date → qualifies (lost deal)
    row = {"brevo_company_id": "abc123", "planhat_id": None, "open_deals": 1, "deal_lost_date": "2024-01-15"}
    qualifies, reason = apply_rules(row)
    assert qualifies is True
    assert reason is None

def test_apply_rules_in_crm_no_planhat_no_deals():
    # In CRM, no planhat_id, zero open deals → qualifies
    row = {"brevo_company_id": "abc123", "planhat_id": None, "open_deals": 0, "deal_lost_date": None}
    qualifies, reason = apply_rules(row)
    assert qualifies is True
    assert reason is None


# ── POST /pipelines/qualify endpoint ─────────────────────────────────────────

MOCK_TECHSTACK_RESPONSE = {
    "domain": "acme.com",
    "tech_score": 10,
    "esp": [{"name": "Mailchimp", "confidence": "high", "source": "spf"}],
    "crm": [], "cms": [], "ecommerce": [],
}

MOCK_BREVO_CRM_RESPONSE = {
    "items": [{"id": "cmp_1", "attributes": {"domain": "acme.com", "ent_planhat_id": None}}]
}


def _make_supabase_mock(sourced_rows=None, qualified_rows=None):
    """
    Returns (mock_sb, sourced_tbl, qualified_tbl) with stable mock objects
    so call assertions work across references.
    """
    sourced_rows = sourced_rows or []
    qualified_rows = qualified_rows or []

    sourced_tbl = MagicMock()
    qualified_tbl = MagicMock()

    # crm_check: .select().not_.is_().is_().execute()
    sourced_tbl.select.return_value.not_.is_.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
    # qualification_rules: .select().execute()
    sourced_tbl.select.return_value.execute.return_value = MagicMock(data=sourced_rows)
    sourced_tbl.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    # technographic: .select().is_().execute()
    qualified_tbl.select.return_value.is_.return_value.execute.return_value = MagicMock(data=qualified_rows)
    qualified_tbl.upsert.return_value.execute.return_value = MagicMock()
    qualified_tbl.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    _tables = {"sourced_tam_v2": sourced_tbl, "qualified_tam_v2": qualified_tbl}
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: _tables.get(name, MagicMock())
    return mock_sb, sourced_tbl, qualified_tbl


@pytest.fixture()
def client():
    mock_sb, sourced_tbl, qualified_tbl = _make_supabase_mock(
        sourced_rows=[{
            "domain": "acme.com", "market": "UK",
            "company_name": "Acme", "brevo_company_id": None,
            "planhat_id": None, "open_deals": 0,
            "deal_lost_date": None, "vertical": "SaaS",
        }],
        qualified_rows=[{"domain": "acme.com", "market": "UK"}],
    )

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb), \
         patch("pipelines.qualification.get_brevo_company", new=AsyncMock(return_value=None)), \
         patch("pipelines.qualification.get_techstack", new=AsyncMock(return_value=MOCK_TECHSTACK_RESPONSE)):
        from api.main import app
        yield TestClient(app), mock_sb, sourced_tbl, qualified_tbl


def test_qualify_endpoint_returns_full_response(client):
    tc, mock_sb, _, __ = client
    resp = tc.post("/pipelines/qualify")
    assert resp.status_code == 200
    body = resp.json()
    assert body["crm"]["status"] == "ok"
    assert body["rules"]["status"] == "ok"
    assert body["technographic"]["status"] == "ok"


def test_qualify_endpoint_new_prospect_qualifies(client):
    tc, _, __, qualified_tbl = client
    tc.post("/pipelines/qualify")
    qualified_tbl.upsert.assert_called_once()
    upserted = qualified_tbl.upsert.call_args[0][0]
    assert upserted[0]["domain"] == "acme.com"


def test_qualify_endpoint_writes_esp(client):
    tc, _, __, qualified_tbl = client
    tc.post("/pipelines/qualify")
    update_payload = qualified_tbl.update.call_args[0][0]
    assert update_payload["esp_detected"] == "Mailchimp"
    assert update_payload["esp_score"] == 100


MOCK_CRM_COMPANY = {
    "brevo_company_id": "cmp_1",
    "open_deals":       2,
    "deal_lost_date":   "2024-03-01",
    "planhat_id":       "ph_99",
}


def test_run_crm_check_writes_all_crm_fields():
    """CRM check calls Brevo API once and writes all four CRM fields to sourced_tam_v2."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"domain": "acme.com", "market": "UK"}]
    )
    mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb), \
         patch("pipelines.qualification.get_brevo_company", new=AsyncMock(return_value=MOCK_CRM_COMPANY)):
        from pipelines.qualification import run_crm_check
        import asyncio
        result = asyncio.run(run_crm_check())

    assert result == {"status": "ok", "processed": 1}
    update_payload = mock_sb.table.return_value.update.call_args[0][0]
    assert update_payload["brevo_company_id"] == "cmp_1"
    assert update_payload["open_deals"] == 2
    assert update_payload["deal_lost_date"] == "2024-03-01"
    assert update_payload["planhat_id"] == "ph_99"


def test_run_crm_check_domain_not_in_crm():
    """Domain not found in CRM → four null fields written to sourced_tam_v2."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"domain": "unknown.com", "market": "UK"}]
    )
    mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb), \
         patch("pipelines.qualification.get_brevo_company", new=AsyncMock(return_value=None)):
        from pipelines.qualification import run_crm_check
        import asyncio
        result = asyncio.run(run_crm_check())

    assert result == {"status": "ok", "processed": 1}
    update_payload = mock_sb.table.return_value.update.call_args[0][0]
    assert update_payload == {
        "brevo_company_id": None,
        "open_deals":       None,
        "deal_lost_date":   None,
        "planhat_id":       None,
    }


def test_run_qualification_rules_disqualifies_customer():
    """Existing customer (has planhat_id) must not appear in qualified_tam_v2 upsert."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
        {"domain": "acme.com", "market": "UK", "company_name": "Acme",
         "brevo_company_id": "cmp_1", "planhat_id": "ph_99",
         "open_deals": 0, "deal_lost_date": None, "vertical": "SaaS"},
    ])

    with patch("pipelines.qualification.get_supabase", return_value=mock_sb):
        from pipelines.qualification import run_qualification_rules
        import asyncio
        result = asyncio.run(run_qualification_rules())

    assert result == {"status": "ok", "qualified": 0, "disqualified": 1}
    mock_sb.table.return_value.upsert.assert_not_called()
