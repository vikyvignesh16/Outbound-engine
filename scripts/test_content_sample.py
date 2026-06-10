"""Run synchronous content generation on a hand-picked sample of contacts.

Used to eyeball the prompt before flipping CONTENT_GENERATION_ENABLED back
to True in pipelines/daily_runner.py. Does NOT write to the database.

Usage:
    source .env && python scripts/test_content_sample.py
    source .env && python scripts/test_content_sample.py --ids c1,c2,c3
    source .env && python scripts/test_content_sample.py --out data/sample.json
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.client import get_supabase, fetch_all  # noqa: E402
from pipelines.content import generate_one  # noqa: E402
from pipelines.news_search import fetch_company_news  # noqa: E402
from pipelines.lp_generator import fetch_company_lp  # noqa: E402


# 5 hand-picked contacts spanning Clay/PB × with-email/no-email × verticals
DEFAULT_IDS = [
    "00006385-e4de-460d-b53d-295449553106",  # Zaheer Ahmed, One Stop, Clay, w/ email, loyalty
    "01b5d0ab-bf04-430b-8575-3caa90e913d4",  # Adil Ladha, Autotrader, Clay, w/ email, no loyalty
    "05e9e5b2-0873-4965-9747-6d2a162f6bb3",  # Gemma Williams, Pets at Home, Clay, no email
    "00adce31-7f8f-4993-b172-1cb178828a97",  # Paul Beiboer, Wahaca, PB, w/ email, hospitality
    "0134578f-5287-4589-bf9a-2b8cfa930f5f",  # Stefan V., Trailfinders, PB, no email, travel
]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="Comma-separated contact UUIDs (defaults to a hand-picked spread)")
    parser.add_argument("--out", type=Path, default=None,
                        help="Optional path to write the JSON results to")
    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else DEFAULT_IDS

    sb = get_supabase()
    contacts = (
        sb.table("sourced_contacts")
        .select("id, domain, email, first_name, last_name, job_title, seniority, "
                "company_name, market, relevance_score, source")
        .in_("id", ids)
        .execute()
        .data
    )

    if not contacts:
        sys.exit(f"No contacts found for ids: {ids}")

    print(f"Loaded {len(contacts)} contacts")
    for c in contacts:
        print(f"  {c['source']:9s}  {c['domain']:35s}  {c['first_name']} {c['last_name']}  ({c['job_title']})")

    # Enrich with priority_tam
    domains = list({c["domain"] for c in contacts})
    company_rows = fetch_all(
        "priority_tam",
        "domain, market, company_name, vertical, account_narrative, account_fit_score, "
        "employee_range, email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "esp_detected, esp_score",
        [("in_", "domain", domains)],
    )
    company_map = {(r["domain"], r.get("market", "")): r for r in company_rows}

    print(f"\nFetching news for {len(domains)} unique domains...")
    news_map: dict[str, dict] = {}
    lp_map: dict[str, str] = {}
    for c in contacts:
        d = (c.get("domain") or "").strip().lower()
        if d and d not in news_map:
            company = company_map.get((c["domain"], c.get("market") or ""), {})
            name = company.get("company_name") or c.get("company_name") or ""
            news = await fetch_company_news(d, name)
            news_map[d] = news
            verdict = "USABLE" if (news.get("found") and news.get("usable")) else "no news"
            print(f"  news {d:35s}  {verdict}  {(news.get('news_summary') or '')[:70]}")

    print(f"\nMinting landing pages for {len(domains)} unique domains (this is slow, 35-45s each)...")
    for c in contacts:
        d = (c.get("domain") or "").strip().lower()
        if d and d not in lp_map:
            company = company_map.get((c["domain"], c.get("market") or ""), {})
            name = company.get("company_name") or c.get("company_name") or ""
            lp_url = await fetch_company_lp(
                domain       = d,
                company_name = name,
                industry     = company.get("vertical"),
                market       = c.get("market") or company.get("market"),
                esp          = company.get("esp_detected"),
            )
            lp_map[d] = lp_url or ""
            tick = "✅" if lp_url else "❌"
            print(f"  lp   {d:35s}  {tick}  {lp_url or '(not minted)'}")

    print("\nGenerating content for each contact (synchronous Messages calls)...")
    results: list[dict] = []
    for c in contacts:
        domain = (c.get("domain") or "").strip().lower()
        company = company_map.get((c["domain"], c.get("market") or ""), {})
        news = news_map.get(domain, {"found": False, "usable": False})
        lp_url = lp_map.get(domain, "")
        try:
            print(f"\n--- {c['first_name']} {c['last_name']} ({c['domain']}) ---")
            content = await generate_one(c, company, news, lp_url=lp_url)
            results.append({
                "contact_id":   c["id"],
                "first_name":   c["first_name"],
                "last_name":    c["last_name"],
                "job_title":    c["job_title"],
                "email":        c.get("email"),
                "domain":       c["domain"],
                "source":       c["source"],
                "news_used":    bool(news.get("found") and news.get("usable")),
                "news_summary": news.get("news_summary"),
                "outbound_content": content,
            })
            print(json.dumps(content, indent=2, ensure_ascii=False))
        except Exception as exc:
            print(f"  ❌ generation failed: {exc}")
            results.append({
                "contact_id": c["id"],
                "error":      str(exc),
            })

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n✅ Wrote {len(results)} results to {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
