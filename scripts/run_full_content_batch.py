"""Kick off content generation for ALL pending sourced_contacts.

Production runner for the full batch (vs scripts/test_content_sample.py
which runs synchronously on a hand-picked few). Calls submit_content() which:
  1. Pre-fetches news per unique domain (concurrent, ~30-60s)
  2. Pre-mints landing pages per unique domain (concurrent, ~12-15 min for ~300)
  3. Submits Claude Batch API in chunks of 500
  4. Returns the batch IDs to monitor

Results land hours later — poll via POST /pipelines/content-complete-all or
wait for the enrich-poller cron (every 30 min) to pick them up.

Usage:
    source .env && python scripts/run_full_content_batch.py
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Stream INFO logs so progress is visible during the LP/news pre-fetch.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
for noisy in ("httpx", "httpcore", "hpack", "anthropic"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


async def main() -> None:
    from pipelines.content import submit_content
    result = await submit_content()
    print()
    print("=" * 60)
    print(f"Status:    {result['status']}")
    print(f"Submitted: {result['submitted']} contacts")
    print(f"Batches:   {result['batches']}")
    for bid in result["batch_ids"]:
        print(f"  - {bid}")
    print("=" * 60)
    print()
    print("Poll for completion via:")
    print("  curl -X POST https://<railway-url>/pipelines/content-complete-all")
    print("Or wait for the enrich-poller cron (every 30 min) to pick them up.")


if __name__ == "__main__":
    asyncio.run(main())
