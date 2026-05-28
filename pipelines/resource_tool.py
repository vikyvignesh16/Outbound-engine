"""
Brevo resource catalogue for outbound content generation.

Each resource is a case study, report, or ebook that Claude selects from
when generating outbound sequence content. Claude receives all resources
and picks the most relevant one based on the contact's vertical and signals.

To add a resource, append a dict to RESOURCES following the schema below.
"""

from typing import Any

# ── Resource catalogue ────────────────────────────────────────────────────────
# ⚠️ Replace placeholders with real Brevo resources before going live.

RESOURCES: list[dict[str, Any]] = [
    {
        "id":                   "buffalo-grill-case-study",
        "company":              "Buffalo Grill",
        "title":                "How Buffalo Grill activated 500,000 loyalty members in 6 months",
        "type":                 "case_study",           # case_study | report | ebook | guide | benchmark
        "industry":             "hospitality",
        "url":                  "https://www.brevo.com/customers/buffalo-grill/",
        "key_metrics":          "500,000 loyalty cards activated in 6 months, 92% retention rate, 75% of signups in-venue via QR code",
        "context":              "Buffalo Grill is a French restaurant chain that needed to unify its loyalty programme with CRM and email marketing. Previously, their loyalty data and email platform were siloed, making personalised communications across 300+ venues extremely difficult.",
        "pain_points":          "Disconnected loyalty and email systems, no unified customer profile, difficulty personalising at scale across multiple venues",
        "brevo_features_tags":  ["loyalty", "email", "CRM", "wallet", "QR"],
        "best_for_verticals":   ["hospitality", "restaurants", "food_beverage", "retail"],
        "best_for_signals":     ["has_loyalty_program", "has_wallet"],
    },
    {
        "id":                   "placeholder-report-1",
        # ⚠️ PLACEHOLDER — replace with a real Brevo report
        "company":              "Brevo",
        "title":                "The 2026 Marketing Automation Benchmark Report",
        "type":                 "report",
        "industry":             "cross-vertical",
        "url":                  "https://www.brevo.com/resources/placeholder-report/",
        "key_metrics":          "Replace with 1-2 headline stats from the report",
        "context":              "Replace with a 1-2 sentence summary of what the report covers and why it matters",
        "pain_points":          "Replace with the core pain points this report addresses",
        "brevo_features_tags":  ["email", "automation", "CRM"],
        "best_for_verticals":   ["saas", "ecommerce", "retail", "fintech"],
        "best_for_signals":     ["needs_cdp"],
    },
    {
        "id":                   "placeholder-ebook-1",
        # ⚠️ PLACEHOLDER — replace with a real Brevo ebook or guide
        "company":              "Brevo",
        "title":                "The Complete Guide to Email and Loyalty Integration",
        "type":                 "ebook",
        "industry":             "retail",
        "url":                  "https://www.brevo.com/resources/placeholder-ebook/",
        "key_metrics":          "Replace with headline outcomes or stats from the ebook",
        "context":              "Replace with what the ebook covers and who it's aimed at",
        "pain_points":          "Replace with the pain points this ebook addresses",
        "brevo_features_tags":  ["loyalty", "email", "CRM"],
        "best_for_verticals":   ["retail", "ecommerce", "hospitality"],
        "best_for_signals":     ["has_loyalty_program"],
    },
]


# ── Tool definition for Claude API ────────────────────────────────────────────

RESOURCE_TOOL_DEFINITION: dict[str, Any] = {
    "name": "search_brevo_resources",
    "description": (
        "Returns all available Brevo case studies, reports, and ebooks. "
        "Review every resource in the result and select the single most relevant one "
        "for this contact, based on their vertical, signal flags (loyalty/CDP/wallet), "
        "and the resource selection rules defined in each email section of the prompt. "
        "Use the selected resource to fill in all resource.* fields when generating content."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vertical": {
                "type": "string",
                "description": "The company's primary vertical or industry",
            },
            "has_loyalty_program": {
                "type": "boolean",
                "description": "True if the company has a loyalty or rewards programme",
            },
            "needs_cdp": {
                "type": "boolean",
                "description": "True if the company shows CDP or unified data signals",
            },
            "has_wallet": {
                "type": "boolean",
                "description": "True if the company has a digital or payment wallet product",
            },
        },
        "required": ["vertical", "has_loyalty_program", "needs_cdp", "has_wallet"],
    },
}


def get_all_resources() -> list[dict[str, Any]]:
    """Returns the full resource catalogue as a list."""
    return RESOURCES
