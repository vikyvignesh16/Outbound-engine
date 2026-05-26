"""
E2E test for the Clay TAM webhook against a live server + real Supabase.

Usage:
    BASE_URL=https://your-app.railway.app python scripts/test_e2e.py

Requires .env with:
    CLAY_WEBHOOK_SECRET, SUPABASE_URL, SUPABASE_SERVICE_KEY
"""
import hmac
import hashlib
import json
import os
import sys

import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
CLAY_SECRET = os.environ["CLAY_WEBHOOK_SECRET"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

TEST_PAYLOAD = [
    {
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
]


def _sign(body: bytes) -> str:
    return hmac.new(CLAY_SECRET.encode(), body, hashlib.sha256).hexdigest()


def run():
    failures = []

    # ── 1. Health check ───────────────────────────────────────────────────────
    print(f"Checking {BASE_URL}/health ...")
    resp = httpx.get(f"{BASE_URL}/health", timeout=10)
    if resp.status_code == 200:
        print("  PASS /health")
    else:
        failures.append(f"/health returned {resp.status_code}")
        print(f"  FAIL /health → {resp.status_code}")

    # ── 2. Webhook POST ───────────────────────────────────────────────────────
    body = json.dumps(TEST_PAYLOAD).encode()
    sig = _sign(body)

    print(f"\nPOSTing to {BASE_URL}/webhooks/clay/tam ...")
    resp = httpx.post(
        f"{BASE_URL}/webhooks/clay/tam",
        content=body,
        headers={"x-clay-signature": sig, "content-type": "application/json"},
        timeout=15,
    )

    if resp.status_code == 200 and resp.json().get("status") == "ok":
        print(f"  PASS webhook → {resp.json()}")
    else:
        failures.append(f"webhook returned {resp.status_code}: {resp.text}")
        print(f"  FAIL webhook → {resp.status_code}: {resp.text}")

    # ── 3. Supabase row verification ──────────────────────────────────────────
    print("\nVerifying Supabase row ...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = (
        sb.table("sourced_tam")
        .select("domain, market, company_name, vertical, country, employee_range, raw")
        .eq("domain", "whitbreadcareers.com")
        .eq("market", "UK")
        .execute()
    )

    if result.data:
        row = result.data[0]
        print("  PASS row found in sourced_tam:")
        for k, v in row.items():
            if k != "raw":
                print(f"    {k}: {v}")
    else:
        failures.append("Row not found in sourced_tam for domain=whitbreadcareers.com, market=UK")
        print("  FAIL row not found in Supabase")

    # ── Result ────────────────────────────────────────────────────────────────
    print()
    if failures:
        print("FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    run()
