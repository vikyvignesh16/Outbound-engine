"""One-off: re-mint landing pages for domains that failed earlier today due to
the LP payload bugs (missing `domain` field, wrong market casing) — both now
fixed in pipelines/lp_generator.py. Reads /tmp/lp_missing_domains.json (built
during the 2026-07-28 incident) and calls fetch_many() for each, which is
cache-first so any domain already resolved elsewhere is a no-op.

FR domains are included but expected to no-op (skipped) since the live LP API
doesn't accept market=FR yet — see lp_generator.py's _MARKET_SLUG comment.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase  # noqa: E402
from pipelines.lp_generator import fetch_many  # noqa: E402


async def main() -> None:
    domains = json.load(open("/tmp/lp_missing_domains.json"))
    targets = [d["domain"] for d in domains]

    sb = get_supabase()
    rows = []
    for i in range(0, len(targets), 200):
        chunk = targets[i:i + 200]
        rows.extend(
            sb.table("priority_tam")
            .select(
                "domain,company_name,vertical,esp_detected,esp_score,account_fit_score,"
                "account_narrative,email_crm_activity,has_wallet,has_loyalty_program,"
                "needs_cdp,icp_archetype_primary,icp_archetype_secondary,icp_archetype_evidence,market"
            )
            .in_("domain", chunk)
            .execute()
            .data
        )
    by_domain = {r["domain"]: r for r in rows}
    print(f"resolved company data for {len(by_domain)}/{len(targets)} domains")

    items = []
    for d in domains:
        pt = by_domain.get(d["domain"])
        if not pt:
            continue
        items.append({
            "domain":                  d["domain"],
            "company_name":            pt.get("company_name"),
            "industry":                pt.get("vertical"),
            "market":                  d["market"],
            "esp_detected":            pt.get("esp_detected"),
            "esp_score":               pt.get("esp_score"),
            "icp_archetype_primary":   pt.get("icp_archetype_primary"),
            "icp_archetype_secondary": pt.get("icp_archetype_secondary"),
            "icp_archetype_evidence":  pt.get("icp_archetype_evidence"),
            "account_fit_reasoning":   pt.get("account_narrative"),
            "account_fit_score":       pt.get("account_fit_score"),
            "has_loyalty_program":     pt.get("has_loyalty_program"),
            "has_wallet":              pt.get("has_wallet"),
            "needs_cdp":               pt.get("needs_cdp"),
            "email_crm_activity":      pt.get("email_crm_activity"),
        })

    print(f"calling fetch_many for {len(items)} domains (FR ones will no-op)...")
    result = await fetch_many(items)
    print(f"minted/cached: {len(result)}/{len(items)}")

    from collections import Counter
    by_market = Counter(d["market"] for d in domains if d["domain"] in result)
    print("succeeded by market:", dict(by_market))
    still_missing = [d["domain"] for d in domains if d["domain"] not in result]
    print(f"still missing: {len(still_missing)}")
    if still_missing:
        print("sample still-missing:", still_missing[:10])


if __name__ == "__main__":
    asyncio.run(main())
