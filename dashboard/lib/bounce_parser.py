"""Parse Lemlist bounce-notification text into a category + severity.

Lemlist ships the full bounce notification email in raw_payload.text (and .html).
We regex out the SMTP response code and map it to a bucket we can act on:

  - hard_recipient_not_found  → "Apollo/Lusha gave us a dead address"
  - hard_blocked              → recipient's gateway blocked us (Mimecast, Proofpoint, etc.)
  - hard_policy_filtered      → marked as spam / policy violation
  - hard_other                → other 5xx with no match
  - soft_mailbox_full         → 4.2.2 / 5.2.2 — try later
  - soft_temp                 → 4xx greylisting / temp deferred
  - unknown                   → couldn't parse

Severity:
  - "hard" — permanent failure; remove from list
  - "soft" — temporary; ok to retry later
  - "unknown" — needs human review
"""
import re

# Pre-compiled patterns (cheap on first import, cheaper on every call)
_SMTP_CODE_RE = re.compile(r"\b([45]\d{2})\s+(\d\.\d\.\d{1,3})\b")
_BARE_5XX_RE  = re.compile(r"\b(5\d{2})\b")
_BARE_4XX_RE  = re.compile(r"\b(4\d{2})\b")

# Substrings (lower-cased text) → (category, severity)
_HARD_RECIPIENT = [
    "recipient not found", "recipientnotfound", "recipient address rejected",
    "user unknown", "no such user", "no such recipient", "no mailbox here",
    "address you entered couldn't be found", "address doesn't exist",
    "is not a valid mailbox", "does not exist", "address not found",
    "550 5.1.1", "550 5.1.10", "550 5.4.1",
]
_HARD_BLOCKED = [
    "blocked using spamhaus", "rejected by mimecast", "proofpoint",
    "barracuda", "sophos pure message",
    "blocked your message", "transaction failed",
    "policy rejection", "your message was blocked",
    "554 5.7.1", "550 5.7.1", "550 5.7.350",
]
_HARD_POLICY = [
    "marked as spam", "identified as spam", "considered as spam",
    "spam content", "spam suspicion",
    "550 5.7.351",
]
_SOFT_FULL = [
    "mailbox full", "quota exceeded", "over quota", "user is over quota",
    "452 4.2.2", "522 5.2.2",
]
_SOFT_TEMP = [
    "greylisted", "greylisting", "deferred", "temporarily deferred",
    "try again later", "temporary local problem",
    "421 4.7", "451 4.7", "450 4.",
]


def parse_bounce(text: str) -> dict:
    """Returns {'category': ..., 'severity': ..., 'smtp_code': ..., 'enhanced_code': ...}."""
    if not text:
        return {"category": "unknown", "severity": "unknown", "smtp_code": None, "enhanced_code": None}

    haystack = text.lower()

    # Try the explicit substring lookups first — they're more specific than raw SMTP codes
    if any(s in haystack for s in _HARD_RECIPIENT):
        category, severity = "hard_recipient_not_found", "hard"
    elif any(s in haystack for s in _HARD_BLOCKED):
        category, severity = "hard_blocked", "hard"
    elif any(s in haystack for s in _HARD_POLICY):
        category, severity = "hard_policy_filtered", "hard"
    elif any(s in haystack for s in _SOFT_FULL):
        category, severity = "soft_mailbox_full", "soft"
    elif any(s in haystack for s in _SOFT_TEMP):
        category, severity = "soft_temp", "soft"
    else:
        category, severity = None, None

    # Pull the first SMTP code if present, even if we already classified
    m = _SMTP_CODE_RE.search(text)
    if m:
        smtp_code, enhanced_code = m.group(1), m.group(2)
    else:
        # Fallback: bare 5xx / 4xx without enhanced status
        m5 = _BARE_5XX_RE.search(text)
        m4 = _BARE_4XX_RE.search(text)
        smtp_code = (m5 or m4).group(1) if (m5 or m4) else None
        enhanced_code = None

    # If we still don't have a category but DID find a code, fall back to severity from the 4xx/5xx prefix
    if category is None:
        if smtp_code and smtp_code.startswith("5"):
            category, severity = "hard_other", "hard"
        elif smtp_code and smtp_code.startswith("4"):
            category, severity = "soft_temp", "soft"
        else:
            category, severity = "unknown", "unknown"

    return {
        "category":      category,
        "severity":      severity,
        "smtp_code":     smtp_code,
        "enhanced_code": enhanced_code,
    }
