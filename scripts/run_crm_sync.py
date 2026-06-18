"""Manual trigger for the priority_tam → Brevo CRM mass push.

Usage:
    source .env && python scripts/run_crm_sync.py --dry-run
    source .env && python scripts/run_crm_sync.py --limit 10
    source .env && python scripts/run_crm_sync.py --market UK
    source .env && python scripts/run_crm_sync.py             # FULL RUN

WARNING: without --dry-run or --limit this performs a real mass push to
Brevo CRM (~2.8k PATCH + ~7.7k POST). One-shot only — see the docstring
in pipelines/crm_sync.py for the no-ID-writeback caveat.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
for noisy in ("httpx", "httpcore", "hpack"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Show first 5 payloads + totals without firing requests.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N rows (smoke testing).")
    parser.add_argument("--market", type=str, default=None,
                        help="Filter to one market (UK / DE / Ireland).")
    args = parser.parse_args()

    from pipelines.crm_sync import sync_priority_tam_to_crm
    result = await sync_priority_tam_to_crm(
        market_filter=args.market,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    print()
    print("=" * 60)
    for k, v in result.items():
        if k == "failures" and v:
            print(f"failures ({len(v)} shown):")
            for f in v[:20]:
                print(f"  {f}")
        else:
            print(f"{k:14s} {v}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
