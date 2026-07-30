import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, BackgroundTasks

from db.client import get_supabase, fetch_all

_BATCH_INPUT_COST_PER_TOKEN  = 1.50 / 1_000_000
_BATCH_OUTPUT_COST_PER_TOKEN = 7.50 / 1_000_000

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _extract_json_object(text: str) -> dict:
    """Finds the outermost top-level JSON object in `text`, tolerating prose
    before/around it. Needed because web_search tool use makes the model
    prone to narrating ("Let me compile the final JSON response...") before
    the answer even when the prompt says not to — naive full-string
    json.loads() or a plain rfind("{") both break on that (rfind finds the
    INNERMOST brace of our nested {"response": {...}} shape, not the outer
    one). Scans left to right, tries a decode at every '{', and accepts the
    first one where nothing but whitespace follows the parsed object."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    decoder = json.JSONDecoder()
    idx = 0
    while True:
        brace = text.find("{", idx)
        if brace == -1:
            raise json.JSONDecodeError("No JSON object found", text, idx)
        try:
            obj, end = decoder.raw_decode(text, brace)
            if text[end:].strip() == "":
                return obj
        except json.JSONDecodeError:
            pass
        idx = brace + 1


# ── Prompt builder ────────────────────────────────────────────────────────────

# Predefined industry taxonomy (confirmed by user). "Other" is the escape
# hatch — see industry_suggestion handling in process_results().
_INDUSTRIES = [
    "Software and IT", "Retail", "Sales, Marketing and Advertising", "Education",
    "Media and Publishing", "Entertainment", "Healthcare and Wellness",
    "Banking and Finance", "NGO", "Automotive, Manufacturing and Construction",
    "Insurance", "Consulting and Agencies", "Travel, Transportation and Tourism",
    "Human Resources, Legal and Accounting", "Real Estate", "Telecom",
    "Energy and Utilities", "Hospitality and Restaurants",
    "Public Administration and Government", "Agriculture and Agribusiness",
    "Storage and Rental Services", "Other",
]

# Confirmed by user.
_BUSINESS_MODELS = ["B2B", "B2C", "B2B2C", "Marketplace", "Nonprofit", "Other"]

# Confirmed by user. Their list tops out at 100,001-500,000 with no open-ended
# band — added "500,001+ employees" as a catch-all so a mega-corp outlier isn't
# forced into the wrong bucket (flagged for review, not silently assumed).
_EMPLOYEE_BANDS = [
    "1-10 employees", "11-50 employees", "51-200 employees",
    "201-500 employees", "501-1,000 employees", "1,001-5,000 employees",
    "5,001-10,000 employees", "10,001-50,000 employees",
    "50,001-100,000 employees", "100,001-500,000 employees",
    "500,001+ employees",
]

# Confirmed by user (values in $M). Same open-ended-top-band gap as employee
# bands above — added "$50B+" as a catch-all, flagged for review.
_REVENUE_BANDS = [
    "$0-1M", "$1-10M", "$10-50M", "$50-100M", "$100-500M", "$500M-1B",
    "$1-5B", "$5-10B", "$10-50B", "$50B+",
]


_ARCHETYPES = ["Graduate", "Network", "Consolidator", "Email Specialist", "Feature Specialist", "Saver", "None"]

_TECH_FIELD_LABELS = [
    ("tech_esp", "Email/ESP"), ("tech_crm", "CRM"), ("tech_cms", "CMS"),
    ("tech_ecommerce", "E-commerce"), ("tech_marketing", "Marketing automation"),
    ("tech_chat", "Chat/conversational"), ("tech_payment", "Payment"),
]


def _build_tech_context(tech_data: dict | None) -> str:
    """Renders already-detected tech_* columns as a grounding block for the
    archetype prompt, so Graduate/Email Specialist/Saver/Consolidator detection
    is based on real DNS/BuiltWith data instead of Claude re-guessing via
    web_search. Returns a "none detected" line if no tech_data was passed."""
    if not tech_data:
        return "  (not yet checked — infer from web search only)"
    lines = []
    for field, label in _TECH_FIELD_LABELS:
        value = tech_data.get(field)
        if value:
            lines.append(f"  - {label}: {value}")
    return "\n".join(lines) if lines else "  (checked — no tools detected in any category)"


# Shared between build_prompt() (full assessment) and build_archetype_prompt()
# (archetype-only, for companies that already have a full fit assessment) so
# the two never drift out of sync.
_ARCHETYPE_RULES_BLOCK = """   A. Graduate — growth straining a basic ESP.
      Signals: on a basic/SMB ESP (Mailchimp, Constant Contact, MailerLite,
      AWeber, lower-tier ActiveCampaign) AND a growth trigger — recent
      Seed/Series A-B funding (last 6-12mo), 30%+ YoY headcount growth, or a
      first dedicated lifecycle hire ("Marketing Automation Manager",
      "Lifecycle/CRM/Email Marketing Manager", "Growth Marketer"), or job
      posts mentioning "scaling"/"building out our martech stack". Common in
      Tech/SaaS, NGO-NFP, Entertainment. Flat/mature growth on the same ESP
      is a Saver, not a Graduate — growth is the tell.

   B. Network — distributed structure, central control breaking down.
      Signals: 5+ physical locations/branded outlets, franchise/multi-location
      language on site ("find a store/agent"), titles like "Franchise
      Marketing Director", "VP Multi-Unit Ops", "Regional/Field Marketing
      Manager", or is a marketing/creative agency managing client accounts
      (team 10-50). Hiring to "standardize/centralize" marketing across
      locations is the trigger, not just the location count alone.

   C. Consolidator — tool sprawl and fragmented data, actively rationalizing.
      Signals: 2+ overlapping martech tools (score on category redundancy,
      not raw count — e.g. two ESPs, or separate SMS+push+CDP tools), a
      recently implemented CDP (Segment, mParticle, Tealium, RudderStack),
      hiring "Marketing Operations", "MarTech Manager", "RevOps", a new
      CMO/CTO/VP Marketing in the last 6mo (leadership change triggers a
      stack review), or public "consolidate/single view" language. Common in
      Retail & Ecommerce, Insurance.

   D. Email Specialist — high-volume/transactional email, engineering owns
      email alongside an existing CRM. THIS ARCHETYPE IS OFTEN B2B OR B2B2C
      BY NATURE — do not penalize it for lacking a "consumer" layer; the
      transactional volume itself is the qualifying signal.
      Signals: a transactional ESP detected (SendGrid, Mailgun, Amazon SES,
      Postmark, SparkPost), dedicated sending subdomains (mail., email.,
      notifications., t.), an inherently high-volume product (marketplace,
      SaaS with notifications, fintech alerts/statements, publisher/
      newsletters, real-estate portal, large e-commerce), hiring
      "Deliverability Engineer", "Email Infrastructure", "Platform/Messaging
      Engineer", or public API docs referencing transactional email/webhooks.
      Common in Publishing, Real Estate, Tech/SaaS.

   E. Feature Specialist — launching a specific capability (loyalty, wallet,
      WhatsApp/conversational) alongside an existing CRM.
      Signals: press/news of a launching loyalty or rewards/membership
      program, /loyalty /rewards /members pages on site, an existing
      point-solution loyalty tool (Yotpo, LoyaltyLion, Smile.io) they may
      want to augment, a consumer mobile app, WhatsApp presence on site or
      HQ/customer base in a WhatsApp-dominant geography (LATAM, India, SEA,
      parts of EMEA), or hiring "Loyalty Manager", "CRM & Loyalty",
      "Retention Marketing", "Conversational Commerce". Common in Retail &
      Ecommerce, QSR, D2C, Travel/Hospitality.

   F. Saver — mature mid-market sender under cost pressure, wants to pay less
      for what they already do, usually around a renewal.
      Signals: on an expensive contact-priced incumbent at scale (HubSpot
      Marketing Pro/Enterprise, Mailchimp with a large list, Klaviyo,
      Salesforce Marketing Cloud, Braze), PE-backed ownership, recent
      cost-cutting/"efficiency" news or layoffs, intent signals like
      "[incumbent] alternatives" or "[incumbent] pricing", or a mature/
      flat-growth company (established age, flat headcount — this is what
      separates Saver from Graduate on the same tool). Common in Retail &
      Ecommerce, Advertising & Marketing.

   Note: some signals (precise headcount growth %, PE ownership, WARN
   filings, third-party intent data) are not reliably verifiable via web
   search — use "None"/skip rather than guess when you cannot find concrete
   evidence."""


def build_archetype_prompt(company_name: str, domain: str, tech_data: dict | None = None,
                            known: dict | None = None) -> str:
    """Much shorter than build_prompt() — for companies that already have a
    full fit assessment (currently: existing priority_tam matches). Industry/
    business_model/employees/revenue are already correct in qualified_tam_v2
    for this population, so they're passed in as KNOWN FACTS rather than
    re-derived, which both shortens the prompt and lets web_search focus
    narrowly on archetype trigger signals instead of general company research
    — the main cost lever, since input/search tokens dominate cost (~90%)."""
    known = known or {}
    tech_context = _build_tech_context(tech_data)

    return f"""You are classifying the Brevo ICP archetype for an ALREADY-QUALIFIED
account — do not re-assess overall fit, only determine which buying-trigger
archetype (if any) applies.

Company: {company_name} ({domain})
Already known — do NOT re-research these, use as given:
  industry: {known.get('industry') or 'unknown'}
  business_model: {known.get('business_model') or 'unknown'}
  employees: {known.get('employees') or 'unknown'}
  revenue: {known.get('company_revenue') or 'unknown'}

Already-detected tech stack (ground truth, do not re-verify):
{tech_context}

Brevo has identified six buying-trigger archetypes. Use web search ONLY to
find evidence for the SPECIFIC trigger signals below — funding, hiring,
multi-location presence, PE ownership, loyalty-programme launches, WhatsApp
presence, or cost-cutting news. Do not spend searches re-confirming the
firmographics already given above.

Classify into ONE or TWO of the following (a company can trip more than one —
pick the strongest as primary), or "None" if no archetype clearly applies.
Do not guess — use "None" if you can't find concrete evidence.

{_ARCHETYPE_RULES_BLOCK}

Return your answer as the LAST thing in your reply, this exact JSON format
with no preamble, no markdown code fences, no text outside it:

{{
  "response": {{
    "icp_archetype_primary": "",
    "icp_archetype_secondary": "",
    "icp_archetype_evidence": ""
  }}
}}"""


def build_prompt(company_name: str, domain: str, industries: list[str] | None = None,
                  tech_data: dict | None = None) -> str:
    industries_list = industries or _INDUSTRIES
    industries_block = "\n".join(f"  - {i}" for i in industries_list)
    models_block = ", ".join(_BUSINESS_MODELS)
    emp_bands_block = ", ".join(_EMPLOYEE_BANDS)
    rev_bands_block = ", ".join(_REVENUE_BANDS)
    tech_context = _build_tech_context(tech_data)

    return f"""You are a sales qualification analyst for Brevo, a CRM and marketing
automation platform used by B2B and B2C companies to manage email,
SMS, and multi-channel marketing campaigns.

Brevo targets companies with 50+ employees that communicate with
customers or users through email, SMS, or CRM workflows.

Use web search to research the company {company_name} ({domain}), then
answer the following:

1. Classify "industry" as EXACTLY ONE of these values (pick the best fit):
{industries_block}
   Use "Other" only if none genuinely fit; if you use "Other", put your
   proposed new category in "industry_suggestion" (else leave it "").

2. "business_model" must be EXACTLY ONE of: {models_block}

3. "employees" must be EXACTLY ONE of these headcount bands (verbatim): {emp_bands_block}
   This MUST be consistent with whatever headcount conclusion you reach in
   your own reasoning for question 8 below — if your reasoning there
   describes the company as "under 50" or "well below 50 employees," this
   field must reflect that same band (e.g. "1-10 employees" or "11-50
   employees"), never a larger one.

4. "company_revenue" must be EXACTLY ONE of these annual-revenue bands, in
   US dollars (verbatim; e.g. "$100-500M" means $100M-$500M annual revenue).
   Estimate the best-fit band from what you find; use "" only if genuinely
   unknown after searching: {rev_bands_block}

5. Does the company operate as multiple brands, subsidiaries, or regional
   entities under one parent (e.g. "Mango France" owned by Mango Group, a
   named regional office of a larger org, a franchise operating under a
   franchisor's brand)? → multi_entity: true | false
   Note: this is a lightweight signal only — it does NOT replace or gate
   priority_tam promotion (that still runs through the separate Domain
   Quality Agent check on domain_status/domain_role).

6. ICP ARCHETYPE — Brevo has identified specific buying-trigger archetypes
   where product fit exists regardless of B2B/B2C status. A company matching
   one of these is NOT automatically a poor fit just for being B2B — the
   archetype match IS the qualifying signal (see the fit-score rubric below).
   Classify into ONE or TWO of the following (a company can trip more than
   one — pick the strongest as primary), or "None" if no archetype clearly
   applies. Do not guess — use "None" if you can't find concrete evidence.

   Already-detected tech stack (ground truth, do not re-verify):
{tech_context}

{_ARCHETYPE_RULES_BLOCK}
   → icp_archetype_primary: one of {_ARCHETYPES}
   → icp_archetype_secondary: same options, or "" if only one or no archetype applies
   → icp_archetype_evidence: one or two sentences citing the specific evidence found

7. Do they likely send emails or manage customer communications?
   Describe what you observe — this is for context only, not scoring.
   Look for any of the following:
   - Marketing newsletters or promotional campaigns
   - Transactional emails (order confirmations, receipts, alerts)
   - Customer onboarding or lifecycle sequences
   - Loyalty or rewards programme communications
   - SMS or multi-channel customer messaging
   - B2B outreach or nurture sequences

8. Are they a good fit for Brevo? Score them 1-5 where:

   IMPORTANT — score based on OBSERVABLE COMMUNICATION ACTIVITY, not on
   business model or entity type. Neither "B2B" nor "government/nonprofit"
   is itself a reason to score low:

   · B2B companies are NOT inherently a poor fit. "B2B" only means their
     customers are other businesses; it says nothing about whether they
     have a communication layer Brevo could serve. Brevo covers B2B needs
     just as much as B2C: CRM and client communications, marketing
     communications (webinars, events, content marketing, nurture
     sequences), transactional emails (onboarding, product/account
     notifications), marketing automation (lead scoring, drip campaigns),
     sales prospecting/outreach, and internal communications — not just
     the B2C-flavored loyalty/wallet signals below. A B2B SaaS company
     running webinars, gated content, or a drip nurture sequence has
     exactly the kind of layer Brevo serves, even with zero consumer-
     facing loyalty or wallet product. If they already run these
     activities on an existing CRM/ESP (HubSpot, Marketo, Salesforce,
     etc.), treat that as a POSITIVE signal — proof of an active
     marketing engine, and a real displacement opportunity, not a
     reason to score lower.

   · Government bodies and nonprofits are NOT inherently a poor fit
     either. If they actively run donor/supporter newsletters,
     fundraising or donation-campaign emails, membership drives, public-
     outreach communications, or event communications, treat that
     exactly like a commercial marketing engine — it is a real,
     qualifying communication layer, not a reason to score low just
     because the entity is non-commercial.

   - 5 = Strong fit — 50+ employees, clear ICP match (retail,
       e-commerce, hospitality, financial services, SaaS, or any
       entity — B2B, B2C, government, or nonprofit — with a
       significant communication layer)
   - 4 = Good fit — 50+ employees, likely sends emails or manages
       customer/client/donor relationships but ICP match is slightly
       less clear
   - 3 = Possible fit — 50+ employees with at least one observable
       signal in ANY of the following:
         · Active email marketing or newsletter programme with an
           engaged subscriber base or community
         · A loyalty or rewards programme (points, tiers, cashback,
           membership cards) — B2C only, not expected of B2B
         · A digital wallet or stored-value product — B2C only
         · Clear need for a Customer Data Platform (multiple channels,
           fragmented data, personalisation at scale)
         · A highly active online community or membership model that
           drives significant recurring communications
         · A subscription-based business model (meal kits, subscription
           boxes, SaaS with consumer users, membership clubs, ticketed
           recurring events) — these inherently require sophisticated
           lifecycle email: welcome sequences, churn prevention, renewal
           reminders, and reactivation flows, making them a strong
           Brevo use case
         · (B2B) An observable marketing/client-communication engine:
           webinars or events, gated content/lead-magnet downloads,
           email nurture/drip sequences to prospects or clients, a
           blog or resource centre feeding an email list, an existing
           CRM/ESP actively used for campaigns (not just internal record-
           keeping), or a dedicated sales-prospecting/outreach operation
         · (Government/nonprofit) An observable donor/supporter
           communication engine: fundraising or donation-campaign
           emails, donor/member newsletters, membership or supporter
           drives, or event/public-outreach communications
   - 2 = Weak fit — 50+ employees but limited observable communication
       activity of any kind (any entity type), no loyalty/wallet/CDP
       signals, no marketing/donor engine, AND no ICP archetype match
       from question 6
   - 1 = Poor fit — score 1 if ANY of the following apply:

       Hard disqualifiers — ALWAYS score 1 regardless of ICP archetype
       or any other signal found; these are NOT overridable:
         · Under 50 employees
         · Individual distributor or franchisee operating under a
           parent brand's infrastructure (e.g. MLM distributors,
           single-agent franchises) with no independent communication
           layer of their own
         · No verifiable digital presence or business identity

       Soft disqualifier — overridable by an ICP archetype match from
       question 6 (especially Email Specialist, Graduate, Consolidator,
       Network, or Saver); if an archetype applies, score 3+ instead:
         · NO observable marketing or communication activity of any
           kind, from ANY entity type — commercial B2B, commercial B2C,
           government body, or nonprofit alike — no webinars/events, no
           content marketing, no email newsletter/campaigns, no CRM-
           driven nurture, no sales-outreach infrastructure, no donor/
           fundraising campaigns (e.g. a quiet back-office contract
           manufacturer, a compliance consultancy, or a government
           office with no discoverable communication footprint at
           all). Neither being B2B nor being a government/nonprofit
           entity is itself disqualifying — the absence of ANY
           communication activity is. If you found even one marketing
           or communication signal, this does NOT apply — score under
           tier 3/4/5 instead based on that signal.

9. Does the company have a digital wallet or payment wallet product?
   (look for signs like a branded wallet, stored value card, prepaid
   account, or in-app payment balance)
   → has_wallet: true | false

10. Does the company run a loyalty or rewards program?
    (look for signs like a points system, membership tiers, rewards
    card, cashback scheme, or loyalty app)
    → has_loyalty_program: true | false

11. Does the company show signs of needing a Customer Data Platform?
    (look for signs like multiple customer touchpoints across channels,
    fragmented data sources, large-scale personalisation activity,
    or job postings mentioning CDP, data unification, or customer 360)
    → needs_cdp: true | false

Important: Do not assume or guess what tools, platforms, or ESPs the
company uses — that is checked separately. Base every answer only on what
you find via web search or already reliably know. If you cannot verify
something, say "unknown" for text fields and false for boolean fields.

You may use web search and reason before your final answer, but your
LAST message must be your answer and nothing else: this exact JSON format
with no preamble, no markdown code fences, and no text outside it:

{{
  "response": {{
    "industry": "",
    "industry_suggestion": "",
    "business_model": "",
    "employees": "",
    "company_revenue": "",
    "multi_entity": false,
    "icp_archetype_primary": "",
    "icp_archetype_secondary": "",
    "icp_archetype_evidence": "",
    "email_crm_activity": "",
    "fit_score": 0,
    "reasoning": "",
    "has_wallet": false,
    "has_loyalty_program": false,
    "needs_cdp": false
  }}
}}"""


# ── Batch helpers ─────────────────────────────────────────────────────────────

def _encode_custom_id(domain: str, market: str, company_name: str = "") -> str:
    raw = f"{domain}||{market}||{company_name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _decode_custom_id(custom_id: str) -> tuple[str, str]:
    """Legacy decode — only used for batches submitted before the hash-based encoding."""
    if "||" in custom_id:
        domain, market = custom_id.split("||", 1)
        return domain, market
    encoded_domain, market = custom_id.rsplit("_", 1)
    return encoded_domain.replace("_", "."), market


def build_batch_requests(
    companies: list[dict],
    industries: list[str] | None = None,
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    return [
        {
            "custom_id": _encode_custom_id(row["domain"], row["market"], row.get("company_name", "")),
            "params": {
                "model": model,
                "max_tokens": 2048,  # was 1000 — web_search tool use + reasoning needs more room than JSON-only did
                "tools": [
                    {"type": "web_search_20250305", "name": "web_search", "max_uses": 3},
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": build_prompt(row.get("company_name", ""), row["domain"], industries=industries, tech_data=row),
                    }
                ],
            },
        }
        for row in companies
    ]


_BATCH_SIZE = 500


# ── Step 5a: submit batch ─────────────────────────────────────────────────────

async def submit_enrichment(
    limit: int | None = None,
    industries: list[str] | None = None,
    model: str = "claude-sonnet-4-6",
    company_keys: list[tuple] | None = None,
    protect_existing_score: bool = False,
) -> dict:
    """
    Reads qualified_tam_v2 rows with no account_fit_score, chunks them into
    batches of 500, submits all chunks in parallel to the Claude Batch API,
    and returns all batch IDs. Pass limit to submit a sample batch only.
    Pass industries to override the default predefined taxonomy (see _INDUSTRIES).
    Pass model to override the default (e.g. a cheaper model for a population
    that needs less reasoning depth).
    Pass company_keys — a list of (domain, market, company_name) tuples — to
    re-enrich a specific population regardless of their current account_fit_score
    (e.g. existing priority_tam matches getting the taxonomy/archetype backfill);
    omit to use the default "no score yet" set.
    Pass protect_existing_score=True so process_results() never writes a lower
    account_fit_score than what's already in qualified_tam_v2 for this batch —
    used for populations already promoted to priority_tam, so a re-score can't
    demote their standing even though priority_tam itself is append-only.
    """
    sb = get_supabase()

    tech_cols = "tech_esp, tech_crm, tech_cms, tech_ecommerce, tech_marketing, tech_chat, tech_payment"

    if company_keys:
        rows = fetch_all("qualified_tam_v2", f"domain, market, company_name, {tech_cols}")
        key_set = set(company_keys)
        rows = [r for r in rows if (r["domain"], r["market"], r.get("company_name")) in key_set]
        if limit:
            rows = rows[:limit]
    elif limit:
        rows = (
            sb.table("qualified_tam_v2")
            .select(f"domain, market, company_name, {tech_cols}")
            .is_("account_fit_score", "null")
            .limit(limit)
            .execute()
            .data
        )
    else:
        rows = fetch_all(
            "qualified_tam_v2",
            f"domain, market, company_name, {tech_cols}",
            [("is_", "account_fit_score", "null")],
        )

    if not rows:
        logger.info("enrichment: no rows to enrich")
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

    client = _get_client()
    chunks = [rows[i: i + _BATCH_SIZE] for i in range(0, len(rows), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(
            requests=build_batch_requests(chunk, industries=industries, model=model)
        )
        mapping = {
            _encode_custom_id(c["domain"], c["market"], c.get("company_name", "")): {
                "domain":       c["domain"],
                "market":       c["market"],
                "company_name": c.get("company_name", ""),
            }
            for c in chunk
        }
        sb.table("enrichment_batches").insert({
            "batch_id":               batch.id,
            "model":                  model,
            "status":                 "pending",
            "companies_submitted":    len(chunk),
            "request_mapping":        mapping,
            "protect_existing_score": protect_existing_score,
        }).execute()
        logger.info("enrichment: submitted batch %s for %d companies (model=%s)", batch.id, len(chunk), model)
        return batch.id

    batch_ids = await asyncio.gather(*[submit_chunk(c) for c in chunks])
    logger.info("enrichment: %d batches submitted, %d companies total", len(batch_ids), len(rows))
    return {"status": "ok", "submitted": len(rows), "batches": len(batch_ids), "batch_ids": list(batch_ids)}


# ── Step 5b: process results ──────────────────────────────────────────────────

async def process_results(batch_id: str) -> dict:
    """
    Checks if the batch is complete. If not, returns {"status": "pending"}.
    If complete, parses results and upserts account_fit_score + signal fields
    into qualified_tam_v2.
    """
    client = _get_client()
    batch = await client.messages.batches.retrieve(batch_id)

    if batch.processing_status != "ended":
        return {"status": "pending", "batch_id": batch_id}

    sb = get_supabase()

    batch_row = (
        sb.table("enrichment_batches")
        .select("request_mapping, protect_existing_score")
        .eq("batch_id", batch_id)
        .execute()
        .data
    )
    request_mapping: dict = batch_row[0]["request_mapping"] if batch_row else {}
    protect_existing_score: bool = bool(batch_row[0].get("protect_existing_score")) if batch_row else False

    updates = []
    total_input = 0
    total_output = 0

    async for result in await client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            logger.warning(
                "enrichment: skipping %s result for %s",
                result.result.type, result.custom_id,
            )
            continue
        try:
            # With the web_search tool, message.content holds multiple blocks
            # (text -> server_tool_use -> web_search_tool_result -> text...),
            # so content[0] is no longer reliably the final answer (and may not
            # even be a text block at all). Take the LAST text block instead —
            # the prompt requires the final message to be JSON-only.
            text_blocks = [b.text for b in result.result.message.content if b.type == "text"]
            if not text_blocks:
                raise IndexError("no text blocks in response")
            # Even the last text block often carries a narrated summary before
            # the JSON despite the prompt saying not to (confirmed live) — pull
            # the JSON object out rather than assuming the block is JSON-only.
            data = _extract_json_object(text_blocks[-1])["response"]
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.error("enrichment: parse error for %s: %s", result.custom_id, exc)
            continue

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        company_info = request_mapping.get(result.custom_id)
        if company_info is not None:
            domain       = company_info["domain"]
            market       = company_info["market"]
            company_name = company_info.get("company_name", "")
        else:
            # Legacy batch submitted before hash-based encoding — fall back to decode
            try:
                domain, market = _decode_custom_id(result.custom_id)
                company_name = ""
            except Exception:
                logger.warning("enrichment: cannot resolve custom_id %s — skipping", result.custom_id)
                continue

        fit_score = data.get("fit_score")
        if not isinstance(fit_score, int) or not (1 <= fit_score <= 5):
            # A tool-use failure (e.g. web_search unavailable during a platform
            # incident) can make the model return fit_score=0 or omit it — the
            # qualified_tam_v2 CHECK constraint only allows 1-5, and an invalid
            # value here would otherwise crash the whole chunk's upsert and
            # discard every other company's results in it. Write NULL instead
            # so this one company is simply left unscored for a future retry.
            if fit_score is not None:
                logger.warning(
                    "enrichment: invalid fit_score %r for %s — writing NULL instead",
                    fit_score, result.custom_id,
                )
            fit_score = None

        updates.append({
            "domain":              domain,
            "market":              market,
            "company_name":        company_name,
            "account_fit_score":   fit_score,
            "vertical":            data.get("industry"),
            "industry_suggestion": data.get("industry_suggestion") or None,
            "business_model":      data.get("business_model") or None,
            "employee_range":      data.get("employees") or None,
            "company_revenue":     data.get("company_revenue") or None,
            "multi_entity":        data.get("multi_entity", False),
            "icp_archetype_primary":   data.get("icp_archetype_primary") or None,
            "icp_archetype_secondary": data.get("icp_archetype_secondary") or None,
            "icp_archetype_evidence":  data.get("icp_archetype_evidence") or None,
            "account_narrative":   data.get("reasoning"),
            "email_crm_activity":  data.get("email_crm_activity"),
            "has_wallet":          data.get("has_wallet", False),
            "has_loyalty_program": data.get("has_loyalty_program", False),
            "needs_cdp":           data.get("needs_cdp", False),
        })

    if protect_existing_score and updates:
        domains = list({u["domain"] for u in updates})
        existing_rows = []
        for i in range(0, len(domains), 200):
            existing_rows.extend(
                sb.table("qualified_tam_v2")
                .select("domain, market, company_name, account_fit_score")
                .in_("domain", domains[i : i + 200])
                .execute()
                .data
            )
        existing_scores = {
            (r["domain"], r["market"], r.get("company_name") or ""): r["account_fit_score"]
            for r in existing_rows
        }
        protected = 0
        for u in updates:
            key = (u["domain"], u["market"], u["company_name"] or "")
            existing_score = existing_scores.get(key)
            if (existing_score is not None and u["account_fit_score"] is not None
                    and u["account_fit_score"] < existing_score):
                u["account_fit_score"] = existing_score
                protected += 1
        if protected:
            logger.info(
                "enrichment: protected %d rows from a lower account_fit_score (batch %s)",
                protected, batch_id,
            )

    write_failures = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i : i + 100]
        try:
            sb.table("qualified_tam_v2").upsert(chunk, on_conflict="domain,market,company_name").execute()
        except Exception:
            # One bad chunk (e.g. an unexpected constraint violation) must not
            # discard every other already-fetched chunk's results — fall back
            # to per-row writes so only the truly bad row(s) are lost.
            for row in chunk:
                try:
                    sb.table("qualified_tam_v2").upsert([row], on_conflict="domain,market,company_name").execute()
                except Exception as row_exc:
                    write_failures += 1
                    logger.error(
                        "enrichment: write failed for %s/%s/%s: %s",
                        row["domain"], row["market"], row["company_name"], row_exc,
                    )
    if write_failures:
        logger.warning("enrichment: %d write failures out of %d results (batch %s)",
                        write_failures, len(updates), batch_id)

    cost = (total_input * _BATCH_INPUT_COST_PER_TOKEN
          + total_output * _BATCH_OUTPUT_COST_PER_TOKEN)

    sb.table("enrichment_batches").update({
        "status":             "completed",
        "companies_enriched": len(updates),
        "input_tokens":       total_input,
        "output_tokens":      total_output,
        "estimated_cost_usd": round(cost, 6),
        "completed_at":       datetime.now(timezone.utc).isoformat(),
    }).eq("batch_id", batch_id).execute()

    logger.info("enrichment: wrote %d results from batch %s (cost: $%.6f)", len(updates), batch_id, cost)
    return {
        "status":              "ok",
        "enriched":            len(updates),
        "input_tokens":        total_input,
        "output_tokens":       total_output,
        "estimated_cost_usd":  round(cost, 6),
    }


# ── Step 5d: archetype-only enrichment (for companies already fully scored) ──

_ARCHETYPE_TECH_COLS = "tech_esp, tech_crm, tech_cms, tech_ecommerce, tech_marketing, tech_chat, tech_payment"


def build_archetype_batch_requests(companies: list[dict], model: str = "claude-sonnet-4-6") -> list[dict]:
    return [
        {
            "custom_id": _encode_custom_id(row["domain"], row["market"], row.get("company_name", "")),
            "params": {
                "model": model,
                "max_tokens": 768,  # far less than the full prompt's 2048 — only 3 short fields to return
                "tools": [
                    {"type": "web_search_20250305", "name": "web_search", "max_uses": 3},
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": build_archetype_prompt(
                            row.get("company_name", ""), row["domain"], tech_data=row,
                            known={
                                "industry":        row.get("vertical"),
                                "business_model":  row.get("business_model"),
                                "employees":       row.get("employee_range"),
                                "company_revenue": row.get("company_revenue"),
                            },
                        ),
                    }
                ],
            },
        }
        for row in companies
    ]


async def submit_archetype_enrichment(
    company_keys: list[tuple] | None = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Archetype-only enrichment for companies that already have a full fit
    assessment — currently: existing priority_tam matches, which already have
    correct industry/business_model/employees/revenue in qualified_tam_v2 (only
    icp_archetype_* is missing/new for them). Pass company_keys — a list of
    (domain, market, company_name) tuples — to scope to a specific population;
    omit to process every qualified_tam_v2 row not yet archetype-classified.
    Pass model to override the default (e.g. a cheaper model for a population
    that needs less reasoning depth).
    """
    sb = get_supabase()

    rows = fetch_all(
        "qualified_tam_v2",
        f"domain, market, company_name, vertical, business_model, employee_range, company_revenue, {_ARCHETYPE_TECH_COLS}",
        [("is_", "icp_archetype_primary", "null")],
    )

    if company_keys:
        key_set = set(company_keys)
        rows = [r for r in rows if (r["domain"], r["market"], r.get("company_name")) in key_set]

    if not rows:
        logger.info("archetype_enrichment: no rows to enrich")
        return {"status": "ok", "submitted": 0, "batches": 0, "batch_ids": []}

    client = _get_client()
    chunks = [rows[i: i + _BATCH_SIZE] for i in range(0, len(rows), _BATCH_SIZE)]

    async def submit_chunk(chunk: list[dict]) -> str:
        batch = await client.messages.batches.create(
            requests=build_archetype_batch_requests(chunk, model=model)
        )
        mapping = {
            _encode_custom_id(c["domain"], c["market"], c.get("company_name", "")): {
                "domain":       c["domain"],
                "market":       c["market"],
                "company_name": c.get("company_name", ""),
            }
            for c in chunk
        }
        sb.table("enrichment_batches").insert({
            "batch_id":            batch.id,
            "model":               model,
            "status":              "pending",
            "companies_submitted": len(chunk),
            "request_mapping":     mapping,
        }).execute()
        logger.info("archetype_enrichment: submitted batch %s for %d companies (model=%s)", batch.id, len(chunk), model)
        return batch.id

    batch_ids = await asyncio.gather(*[submit_chunk(c) for c in chunks])
    logger.info("archetype_enrichment: %d batches submitted, %d companies total", len(batch_ids), len(rows))
    return {"status": "ok", "submitted": len(rows), "batches": len(batch_ids), "batch_ids": list(batch_ids)}


async def process_archetype_results(batch_id: str) -> dict:
    """Like process_results(), but writes ONLY icp_archetype_* via a targeted
    per-row update — never touches account_fit_score/vertical/business_model/
    etc., since those are already correct for this population and must not
    risk being clobbered. Each write is isolated (same lesson as technographic:
    one bad write must not discard the rest of a mostly-successful batch)."""
    client = _get_client()
    batch = await client.messages.batches.retrieve(batch_id)

    if batch.processing_status != "ended":
        return {"status": "pending", "batch_id": batch_id}

    sb = get_supabase()
    batch_row = (
        sb.table("enrichment_batches")
        .select("request_mapping")
        .eq("batch_id", batch_id)
        .execute()
        .data
    )
    request_mapping: dict = batch_row[0]["request_mapping"] if batch_row else {}

    updates = []
    total_input = 0
    total_output = 0

    async for result in await client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            logger.warning("archetype_enrichment: skipping %s result for %s", result.result.type, result.custom_id)
            continue
        try:
            text_blocks = [b.text for b in result.result.message.content if b.type == "text"]
            if not text_blocks:
                raise IndexError("no text blocks in response")
            data = _extract_json_object(text_blocks[-1])["response"]
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.error("archetype_enrichment: parse error for %s: %s", result.custom_id, exc)
            continue

        usage = result.result.message.usage
        total_input  += usage.input_tokens
        total_output += usage.output_tokens

        info = request_mapping.get(result.custom_id)
        if info is None:
            logger.warning("archetype_enrichment: cannot resolve custom_id %s — skipping", result.custom_id)
            continue

        updates.append({
            "domain":                  info["domain"],
            "market":                  info["market"],
            "company_name":            info.get("company_name", ""),
            "icp_archetype_primary":   data.get("icp_archetype_primary") or None,
            "icp_archetype_secondary": data.get("icp_archetype_secondary") or None,
            "icp_archetype_evidence":  data.get("icp_archetype_evidence") or None,
        })

    write_failures = 0
    for u in updates:
        try:
            (
                sb.table("qualified_tam_v2")
                .update({
                    "icp_archetype_primary":   u["icp_archetype_primary"],
                    "icp_archetype_secondary": u["icp_archetype_secondary"],
                    "icp_archetype_evidence":  u["icp_archetype_evidence"],
                })
                .eq("domain", u["domain"]).eq("market", u["market"]).eq("company_name", u["company_name"])
                .execute()
            )
        except Exception as exc:
            write_failures += 1
            logger.error("archetype_enrichment: write failed for %s/%s: %s — left for retry", u["domain"], u["market"], exc)

    cost = (total_input * _BATCH_INPUT_COST_PER_TOKEN
          + total_output * _BATCH_OUTPUT_COST_PER_TOKEN)

    sb.table("enrichment_batches").update({
        "status":             "completed",
        "companies_enriched": len(updates) - write_failures,
        "input_tokens":       total_input,
        "output_tokens":      total_output,
        "estimated_cost_usd": round(cost, 6),
        "completed_at":       datetime.now(timezone.utc).isoformat(),
    }).eq("batch_id", batch_id).execute()

    logger.info("archetype_enrichment: wrote %d results (%d write failures) from batch %s (cost: $%.6f)",
                len(updates) - write_failures, write_failures, batch_id, cost)
    return {
        "status":              "ok",
        "processed":           len(updates) - write_failures,
        "write_failures":      write_failures,
        "input_tokens":        total_input,
        "output_tokens":       total_output,
        "estimated_cost_usd":  round(cost, 6),
    }


# ── Step 6: Prioritize ────────────────────────────────────────────────────────

async def run_prioritize() -> dict:
    """
    Reads qualified_tam_v2 rows with account_fit_score >= 3 and upserts them
    into priority_tam. Filters out rows the Domain Quality Agent has flagged
    as subsidiaries or bogus — these should not be contacted (head office
    gets contacted instead).

    NULL domain_status is permitted so rows pending first agent check still
    flow through. Once domain_quality_checked_at is populated for everything,
    the NULL case becomes empty.
    """
    sb = get_supabase()

    # NOTE: brevo_company_id is INTENTIONALLY EXCLUDED from the SELECT.
    #
    # On 2026-06-25 we discovered ~6,000 duplicate CRM records were created
    # because this upsert was overwriting priority_tam.brevo_company_id with
    # NULL values from qualified_tam_v2 (where CRM check hadn't seen the
    # newly-created record yet). The next crm_sync run then saw NULL IDs and
    # POSTed everything again, creating duplicates.
    #
    # Excluding brevo_company_id from the upsert payload preserves whatever
    # value priority_tam currently has — including IDs written back by
    # crm_sync after a CREATE. PATCHes still use these IDs correctly.
    rows = fetch_all(
        "qualified_tam_v2",
        "domain, market, company_name, company_type, employee_range, "
        "location, country, linkedin_url, vertical, tam_segment, "
        "business_model, company_revenue, multi_entity, "
        "icp_archetype_primary, icp_archetype_secondary, icp_archetype_evidence, "
        "planhat_id, open_deals, deal_lost_date, "
        "esp_detected, esp_score, account_fit_score, account_narrative, "
        "email_crm_activity, has_wallet, has_loyalty_program, needs_cdp, "
        "domain_status, domain_role, "
        "tech_score, tech_stack_primary, tech_category, tech_esp, tech_crm, "
        "tech_cms, tech_ecommerce, tech_analytics, tech_cdn, tech_payment, "
        "tech_marketing, tech_chat, tech_hosting, tech_ab_testing, tech_tag_manager",
        [("gte", "account_fit_score", 3)],
    )

    # Domain Quality Agent gate — block subsidiaries, branches, franchisees, bogus.
    _BLOCKED_STATUS = {"subsidiary", "bogus"}
    _BLOCKED_ROLE   = {"property", "branch", "franchisee"}

    eligible = [
        r for r in rows
        if (r.get("domain_status") not in _BLOCKED_STATUS)
        and (r.get("domain_role")   not in _BLOCKED_ROLE)
    ]
    skipped = len(rows) - len(eligible)
    logger.info("prioritize: %d eligible after domain-quality gate (skipped %d)",
                len(eligible), skipped)

    if not eligible:
        return {"status": "ok", "prioritized": 0, "skipped_by_gate": skipped}

    # Drop the gate columns before upsert — priority_tam doesn't have them
    for r in eligible:
        r.pop("domain_status", None)
        r.pop("domain_role",   None)

    for i in range(0, len(eligible), 100):
        chunk = eligible[i : i + 100]
        sb.table("priority_tam").upsert(chunk, on_conflict="domain,market,company_name").execute()

    logger.info("prioritize: upserted %d rows into priority_tam", len(eligible))
    return {"status": "ok", "prioritized": len(eligible), "skipped_by_gate": skipped}


# ── Step 5c: poll all pending batches ────────────────────────────────────────

async def process_all_pending() -> dict:
    """
    Polls all pending enrichment batches.
    If any are still processing, returns still_pending count.
    Once all complete, runs prioritize.
    """
    from utils.slack import notify

    try:
        sb = get_supabase()

        pending = (
            sb.table("enrichment_batches")
            .select("batch_id")
            .eq("status", "pending")
            .execute()
            .data
        )

        if not pending:
            return {
                "status": "ok",
                "message": "no_pending_batches",
                "processed": 0,
                "still_pending": 0,
                "prioritize": None,
            }

        still_pending = 0
        total_enriched = 0

        for row in pending:
            result = await process_results(row["batch_id"])
            if result["status"] == "pending":
                still_pending += 1
            else:
                total_enriched += result.get("enriched", 0)

        if still_pending > 0:
            return {
                "status":         "ok",
                "processed":      len(pending) - still_pending,
                "still_pending":  still_pending,
                "total_enriched": total_enriched,
                "prioritize":     None,
            }

        # All batches done — run prioritize
        prioritize_result = await run_prioritize()

        # Build score + ESP breakdown from DB
        score_rows = (
            sb.table("qualified_tam_v2")
            .select("account_fit_score")
            .not_.is_("account_fit_score", "null")
            .execute()
            .data
        )
        from collections import Counter
        score_counts = Counter(r["account_fit_score"] for r in score_rows)
        score_line = " | ".join(f"{s}★ {score_counts[s]}" for s in sorted(score_counts, reverse=True))

        esp_rows = (
            sb.table("qualified_tam_v2")
            .select("esp_detected")
            .not_.is_("esp_detected", "null")
            .execute()
            .data
        )
        esp_counts = Counter(r["esp_detected"] for r in esp_rows)
        top_esp = sorted(esp_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        esp_line = " | ".join(f"{e} {c}" for e, c in top_esp)

        await notify(
            f"✅ *Enrichment complete*\n"
            f"• Enriched: {total_enriched} companies\n"
            f"• Fit scores: {score_line}\n"
            f"• ESP detected: {esp_line or 'none'}\n"
            f"• Priority TAM: {prioritize_result['prioritized']} companies pushed"
        )

        return {
            "status":         "ok",
            "processed":      len(pending),
            "still_pending":  0,
            "total_enriched": total_enriched,
            "prioritize":     prioritize_result,
        }

    except Exception as exc:
        await notify(f"❌ *Enrich poller failed* — `{exc}`", success=False)
        raise


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/pipelines/enrich")
async def enrich(limit: int | None = None):
    """Submits qualified_tam_v2 rows to Claude Batch API. Pass ?limit=100 for a sample run."""
    return await submit_enrichment(limit=limit)


@router.post("/pipelines/enrich/complete")
async def enrich_complete(batch_id: str):
    """Processes results for a completed batch. Returns pending if not done yet."""
    return await process_results(batch_id)


@router.post("/pipelines/enrich-complete-all")
async def enrich_complete_all():
    """Polls all pending batches. Runs prioritize + dbt once all are done."""
    return await process_all_pending()


async def _run_prioritize_background() -> None:
    """Wraps run_prioritize() for BackgroundTasks — the HTTP request that
    triggers this returns immediately, so failures/results have to surface
    via logging + Slack rather than the response body. Needed because this
    can take longer to run than the platform's request/gateway timeout,
    which was silently killing the synchronous version mid-run (observed
    2026-07-21: repeated /pipelines/prioritize calls died at the identical
    row count every time, never progressing further)."""
    from utils.slack import notify

    try:
        result = await run_prioritize()
        await notify(
            f"✅ *Prioritize complete* — {result['prioritized']} rows upserted into "
            f"priority_tam ({result['skipped_by_gate']} skipped by domain-quality gate)"
        )
    except Exception as exc:
        logger.exception("prioritize: background run failed")
        await notify(f"❌ *Prioritize failed* — `{exc}`", success=False)


@router.post("/pipelines/prioritize")
async def prioritize(background_tasks: BackgroundTasks):
    """Promotes qualified_tam_v2 rows with fit score >= 3 into priority_tam.
    Runs in the background — the request returns immediately; check Slack
    or priority_tam row counts for completion."""
    background_tasks.add_task(_run_prioritize_background)
    return {"status": "ok", "message": "started_in_background"}
