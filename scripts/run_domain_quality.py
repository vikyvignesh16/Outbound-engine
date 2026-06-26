"""Manual trigger for the Domain Quality Agent.

Runs the Claude-Haiku-4.5 + web_search agent over qualified_tam_v2 rows
where domain_quality_checked_at IS NULL. Concurrency capped at 5.

Usage:
    source .env && python scripts/run_domain_quality.py --limit 5     # smoke test
    source .env && python scripts/run_domain_quality.py --limit 100   # batch
    source .env && python scripts/run_domain_quality.py               # all pending
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
for noisy in ("httpx", "httpcore", "anthropic", "hpack"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N rows. Omit to process all pending.")
    parser.add_argument("--parked-only", action="store_true",
                        help="Restrict to rows present in priority_tam_parked (shared-domain triage).")
    args = parser.parse_args()

    from pipelines.domain_quality import run_domain_quality_check
    result = await run_domain_quality_check(limit=args.limit, parked_only=args.parked_only)

    print()
    print("=" * 60)
    for k, v in result.items():
        print(f"{k:22s} {v}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
