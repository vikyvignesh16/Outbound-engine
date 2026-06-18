"""Classify all unprocessed Lemlist replies into reply_classifications.

Manual trigger for the reply_intelligence pipeline. Idempotent — skips
replies already classified (matched by lemlist_activity_id).

Usage:
    source .env && python scripts/run_reply_classifier.py
    source .env && python scripts/run_reply_classifier.py --limit 5  # test on 5 first
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


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N pending replies (for sample testing).")
    args = parser.parse_args()

    from pipelines.reply_intelligence import classify_pending_replies
    result = await classify_pending_replies(limit=args.limit)
    print()
    print("=" * 60)
    print(f"Status:    {result['status']}")
    print(f"Processed: {result['processed']}")
    print(f"Written:   {result['written']}")
    print(f"Failed:    {result.get('failed', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
