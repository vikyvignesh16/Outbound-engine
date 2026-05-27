from pydantic import BaseModel, Field, RootModel, field_validator
from typing import Optional, List, Any
from datetime import datetime

COUNTRY_TO_MARKET: dict[str, str] = {
    "united kingdom": "UK",
    "france": "FR",
    "united states": "US",
    "germany": "DE",
    "spain": "ES",
    "italy": "IT",
    "netherlands": "NL",
    "belgium": "BE",
    "sweden": "SE",
    "denmark": "DK",
    "norway": "NO",
    "finland": "FI",
    "switzerland": "CH",
    "austria": "AT",
    "portugal": "PT",
    "poland": "PL",
}

# ── Clay TAM ──────────────────────────────────────────────────────────────────

class ClayTAMRow(BaseModel):
    model_config = {"populate_by_name": True}

    name: str                   = Field(alias="Name")
    company_type: Optional[str] = Field(None, alias="Type")
    size: Optional[str]         = Field(None, alias="Size")
    location: Optional[str]     = Field(None, alias="Location")
    country: Optional[str]      = Field(None, alias="Country")
    linkedin_url: Optional[str] = Field(None, alias="LinkedIn URL")
    domain: str                 = Field(alias="Domain")
    vertical: Optional[str]     = Field(None, alias="Primary Industry")
    def market(self) -> str:
        return COUNTRY_TO_MARKET.get((self.country or "").lower(), self.country or "UNKNOWN")

class ClayTAMPayload(RootModel[List[ClayTAMRow]]):
    pass

# ── Clay Contacts ─────────────────────────────────────────────────────────────

class ClayContactRow(BaseModel):
    # ⚠️ PENDING: update field names from real Clay contacts payload
    domain: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None

class ClayContactsPayload(BaseModel):
    run_id: str
    rows: List[ClayContactRow]

# ── Albacross ─────────────────────────────────────────────────────────────────

class AlbacrossPayload(BaseModel):
    # ⚠️ PENDING: update field names from real Albacross payload
    domain: str
    occurred_at: datetime
    raw_data: Any = None

# ── Lemlist ───────────────────────────────────────────────────────────────────

class LemlistPayload(BaseModel):
    # ⚠️ PENDING: update field names from real Lemlist payload
    email: str
    event_type: str
    occurred_at: datetime
    raw_data: Any = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {"email_open", "email_click", "reply", "bounce", "unsubscribe"}
        if v not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v
