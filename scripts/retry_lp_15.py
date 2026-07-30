"""Retry the 15 US/FR domains that hit transient errors during the
2026-07-28 full 535-domain LP regeneration. Runs at low concurrency
(3 in flight, vs fetch_many's default 15) since these failures looked
load-related on the external service's side, same as the earlier 28-domain
retry. Unlike that one, this set is mixed market (US + FR), so each
domain's own market from /tmp/lp_retry_15.json is used rather than a
single hardcoded value."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase  # noqa: E402
from pipelines.lp_generator import fetch_company_lp  # noqa: E402


async def main() -> None:
    targets = json.load(open("/tmp/lp_retry_15.json"))
    market_by = {t["domain"]: t["market"] for t in targets}
    domains = list(market_by.keys())

    sb = get_supabase()
    rows = (
        sb.table("priority_tam")
        .select(
            "domain,company_name,vertical,esp_detected,esp_score,account_fit_score,"
            "account_narrative,email_crm_activity,has_wallet,has_loyalty_program,"
            "needs_cdp,icp_archetype_primary,icp_archetype_secondary,icp_archetype_evidence"
        )
        .in_("domain", domains)
        .execute()
        .data
    )
    by_domain = {r["domain"]: r for r in rows}
    print(f"resolved {len(by_domain)}/{len(domains)} domains")

    sem = asyncio.Semaphore(3)
    succeeded, failed = [], []

    async def _one(domain: str) -> None:
        pt = by_domain.get(domain)
        if not pt:
            failed.append(domain)
            return
        async with sem:
            url = await fetch_company_lp(
                domain=domain,
                company_name=pt.get("company_name"),
                industry=pt.get("vertical"),
                market=market_by[domain],
                esp=pt.get("esp_detected"),
                icp_archetype_primary=pt.get("icp_archetype_primary"),
                icp_archetype_secondary=pt.get("icp_archetype_secondary"),
                icp_archetype_evidence=pt.get("icp_archetype_evidence"),
                account_fit_reasoning=pt.get("account_narrative"),
                account_fit_score=pt.get("account_fit_score"),
                esp_score=pt.get("esp_score"),
                has_loyalty_program=pt.get("has_loyalty_program"),
                has_wallet=pt.get("has_wallet"),
                needs_cdp=pt.get("needs_cdp"),
                email_crm_activity=pt.get("email_crm_activity"),
            )
            (succeeded if url else failed).append(domain)

    await asyncio.gather(*[_one(d) for d in domains])
    print(f"succeeded: {len(succeeded)}/{len(domains)}")
    if failed:
        print("still failed:", failed)


if __name__ == "__main__":
    asyncio.run(main())
