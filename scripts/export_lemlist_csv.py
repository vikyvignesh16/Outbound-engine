"""Export batch 1 contacts to a single Lemlist-ready CSV.

Produces one file with all 1,134 contacts:
  - data/batch1_lemlist.csv

Each row carries the standard Lemlist contact fields (email, first_name,
last_name, linkedin_url, company_name) plus every outbound_content field
referenced in the Lemlist template (subject lines, paragraphs, body+cta
splits, resource URLs, personalised LP URL). The `channel` column tags
each row as "email" (959), "linkedin_only" (175), or "none" so you can
filter at upload time if you want to split into separate Lemlist campaigns.

LinkedIn URLs in sourced_contacts are normalised (no scheme, no www).
This script reconstructs them as https://www.linkedin.com/in/<slug> so
Lemlist's LinkedIn extension can open the profile.

Usage:
    source .env && python scripts/export_lemlist_csv.py
"""
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
for noisy in ("httpx", "httpcore"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

from db.client import fetch_all  # noqa: E402

logger = logging.getLogger("export_lemlist_csv")

# Columns: standard Lemlist contact fields first, then outbound_content fields
# in sequence order. Names here are the {{template variables}} you reference
# in your Lemlist campaign template bodies.
STANDARD = ["email", "first_name", "last_name", "linkedin_url", "company_name", "domain", "market", "channel"]

CONTENT_FIELDS = [
    # Email 1 (Day 1)
    "subject_line_1",
    "email_1_paragraph_1",
    "email_1_paragraph_2",
    "email_1_lp_teaser",
    "personalised_lp_url",
    "email_1_p3_body",
    "email_1_p3_cta",
    # LinkedIn 1 (Day 3)
    "linkedin_message_1",
    # Email 2 (Day 7)
    "subject_line_2",
    "email_2_hook",
    "email_2_paragraph_1",
    "email_2_p2_body",
    "email_2_p2_cta",
    "selected_resource_email2_url",
    "selected_resource_email2_title",
    # Email 3 (Day 12)
    "subject_line_3",
    "email_3_paragraph_1",
    "email_3_p2_body",
    "email_3_p2_cta",
    "selected_resource_email3_url",
    "selected_resource_email3_title",
    # LinkedIn 2 (Day 13)
    "linkedin_message_2",
    # Email 4 (Day 18)
    "subject_line_4",
    "email_4_paragraph_1",
    "email_4_p2_body",
    "email_4_p2_cta",
]

ALL_COLUMNS = STANDARD + CONTENT_FIELDS


def _reconstruct_linkedin_url(normalised: str | None) -> str:
    """linkedin.com/in/foo → https://www.linkedin.com/in/foo (Lemlist needs full URL)."""
    if not normalised:
        return ""
    u = normalised.strip()
    if u.startswith(("http://", "https://")):
        return u
    return f"https://www.{u}" if not u.startswith("www.") else f"https://{u}"


def _flatten(contact: dict) -> dict:
    oc = contact.get("outbound_content") or {}
    email = (contact.get("email") or "").strip()
    li = _reconstruct_linkedin_url(contact.get("linkedin_url"))
    if email:
        channel = "email"
    elif li:
        channel = "linkedin_only"
    else:
        channel = "none"
    row = {
        "email":          email,
        "first_name":     contact.get("first_name") or "",
        "last_name":      contact.get("last_name") or "",
        "linkedin_url":   li,
        "company_name":   contact.get("company_name") or "",
        "domain":         contact.get("domain") or "",
        "market":         contact.get("market") or "",
        "channel":        channel,
    }
    for f in CONTENT_FIELDS:
        v = oc.get(f, "")
        # Normalise newlines so the CSV stays clean across platforms
        if isinstance(v, str):
            v = v.replace("\r\n", "\n").strip()
        row[f] = v if v is not None else ""
    return row


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %d rows → %s (%d bytes)", len(rows), path, path.stat().st_size)


def main() -> None:
    logger.info("loading batch-1 contacts with generated content...")
    contacts = fetch_all(
        "sourced_contacts",
        "id, email, first_name, last_name, linkedin_url, company_name, "
        "domain, market, outbound_content, content_generated_at",
        [("eq", "batch_number", 1)],
    )
    with_content = [c for c in contacts if c.get("content_generated_at") and c.get("outbound_content")]
    logger.info("loaded %d total, %d with generated content", len(contacts), len(with_content))

    flattened = [_flatten(c) for c in with_content]

    by_channel = {"email": 0, "linkedin_only": 0, "none": 0}
    for r in flattened:
        by_channel[r["channel"]] += 1

    logger.info("channel split: %d email, %d linkedin_only, %d none",
                by_channel["email"], by_channel["linkedin_only"], by_channel["none"])

    data_dir = Path(__file__).resolve().parents[1] / "data"
    _write_csv(data_dir / "batch1_lemlist.csv", flattened)

    print()
    print("=" * 60)
    print(f"✅ Wrote {len(flattened):4d} contacts → data/batch1_lemlist.csv")
    print(f"   channel breakdown: {by_channel['email']} email | "
          f"{by_channel['linkedin_only']} linkedin_only | {by_channel['none']} none")
    print("=" * 60)
    print()
    print("In Lemlist, filter on the `channel` column at upload to split into")
    print("campaigns — e.g. channel=email for the full 6-step sequence and")
    print("channel=linkedin_only for the LinkedIn-only 2-step sequence.")


if __name__ == "__main__":
    main()
