"""
Test batch: 11 leads from the UKI evaluation CSV.
Runs all content generation calls in parallel and writes output_sequences.csv.
"""
import asyncio
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipelines.resource_tool import select_resource
from pipelines.content import _build_content_prompt
import anthropic

LEADS = [
    {
        "contact": {
            "first_name": "Francesca", "last_name": "Albani",
            "job_title": "CRM Manager",
            "domain": "harrodscareers.com", "company_name": "Harrods", "market": "UK",
        },
        "company": {
            "domain": "harrodscareers.com", "company_name": "Harrods",
            "vertical": "luxury retail",
            "esp_detected": None, "esp_score": 0,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": True,
            "account_fit_score": 5,
            "account_narrative": (
                "Harrods is a large luxury retailer with 5,000+ employees. They operate in retail, "
                "a core Brevo ICP vertical. They have a confirmed loyalty programme (Harrods Rewards), "
                "a stored-value/prepaid card product, high-volume transactional communications, and "
                "seasonal marketing campaigns. Multiple customer touchpoints across in-store, online, "
                "app, and loyalty channels signal fragmented data and a likely need for data unification "
                "and personalisation at scale."
            ),
            "email_crm_activity": (
                "Harrods operates the Harrods Rewards loyalty programme with tiered membership, "
                "which implies lifecycle email communications, points balance updates, and tier-upgrade "
                "notifications. They run promotional campaigns aligned with seasonal events. "
                "As a high-volume retailer, transactional emails (order confirmations, shipping, receipts) "
                "are highly active. They operate a gift card and stored-value product (the Harrods "
                "Knightsbridge Card). SMS and multi-channel messaging are plausible given their loyalty "
                "app and digital presence."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Rebecca", "last_name": "Bath",
            "job_title": "Lifecycle Marketing Manager",
            "domain": "deliveroo.co.uk", "company_name": "Deliveroo", "market": "UK",
        },
        "company": {
            "domain": "deliveroo.co.uk", "company_name": "Deliveroo",
            "vertical": "food delivery",
            "esp_detected": "Mailchimp", "esp_score": 100,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Deliveroo is a large-scale consumer-facing platform operating in food delivery. "
                "They have an extensive customer communication layer spanning transactional email, SMS, "
                "push notifications, promotional campaigns, subscription lifecycle messaging (Deliveroo Plus), "
                "and B2B partner communications. The volume and variety of their customer touchpoints "
                "across multiple channels make them an excellent candidate for a CRM and marketing "
                "automation platform."
            ),
            "email_crm_activity": (
                "Deliveroo operates a high-volume, multi-channel customer communication layer. "
                "Observable signals: transactional emails for order confirmations, receipts, and delivery "
                "status; promotional campaigns for discounts and seasonal offers; Deliveroo Plus subscription "
                "communications (renewal reminders, member benefits); SMS and push notification alerts for "
                "order tracking; B2B onboarding sequences for restaurant and grocery partners; "
                "rider communications for fleet management."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Sophie", "last_name": "Thompson",
            "job_title": "Email Marketing Manager",
            "domain": "futureplc.com", "company_name": "Future", "market": "UK",
        },
        "company": {
            "domain": "futureplc.com", "company_name": "Future",
            "vertical": "media and digital publishing",
            "esp_detected": "Google Workspace", "esp_score": 50,
            "has_loyalty_program": False, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Future plc is a large publicly listed media and digital publishing company with ~3,500 "
                "employees operating dozens of consumer-facing brands (TechRadar, PC Gamer, Homes & Gardens). "
                "They have millions of registered users across subscription products, e-commerce affiliate "
                "commerce, and editorial newsletters. Their business model relies on audience retention, "
                "subscription renewals, and commerce engagement — creating complex CRM segmentation and "
                "automation needs across multiple brands."
            ),
            "email_crm_activity": (
                "Future plc runs subscription-based products across many titles, implying transactional "
                "emails (subscription confirmations, renewals, billing alerts). Their e-commerce and affiliate "
                "commerce activity drives product recommendation emails and promotional newsletters. "
                "Several brands operate newsletters and editorial digests. Audience registration flows "
                "on properties like TechRadar involve onboarding and lifecycle email sequences. "
                "Multi-brand complexity across dozens of brands with millions of registered users "
                "creates significant CRM requirements."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Rebecca", "last_name": "Lee",
            "job_title": "Marketing Manager - Premium Country Pubs",
            "domain": "mbplc.com", "company_name": "Mitchells & Butlers", "market": "UK",
        },
        "company": {
            "domain": "mbplc.com", "company_name": "Mitchells & Butlers",
            "vertical": "hospitality",
            "esp_detected": "SparkPost", "esp_score": 75,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Mitchells & Butlers is one of the UK's largest operators of restaurants, pubs, and bars "
                "(All Bar One, Harvester, Toby Carvery, Miller & Carter) with ~44,000 employees and 1,700+ "
                "venues across 15+ consumer brands. They run an active loyalty programme, brand-level email "
                "marketing, online reservations triggering transactional communications, and multi-channel "
                "CRM orchestration. The multi-brand structure creates clear use cases for segmentation, "
                "lifecycle marketing, and personalisation."
            ),
            "email_crm_activity": (
                "Mitchells & Butlers: marketing newsletters and promotional campaigns delivered via individual "
                "brand websites; loyalty and rewards programme communications via their Reward app; "
                "transactional and booking-related emails through online reservation systems; "
                "SMS plausible given loyalty app infrastructure; 15+ distinct consumer-facing brands "
                "each with their own customer base suggests segmented CRM at scale."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Trevor", "last_name": "Johnstone",
            "job_title": "Head of CRM",
            "domain": "telegraph.co.uk", "company_name": "The Telegraph", "market": "UK",
        },
        "company": {
            "domain": "telegraph.co.uk", "company_name": "The Telegraph",
            "vertical": "media and publishing",
            "esp_detected": "Google Workspace", "esp_score": 50,
            "has_loyalty_program": False, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "The Telegraph is a large subscription-based digital media business with a significant "
                "customer communication layer. Their model involves transactional emails, editorial "
                "newsletters, subscriber lifecycle sequences, onboarding flows, and promotional campaigns. "
                "Their focus on subscriber acquisition and retention mirrors patterns seen in SaaS and "
                "e-commerce. They operate a digital subscription model (Telegraph Premium) with paywall "
                "mechanics and free trial conversion sequences."
            ),
            "email_crm_activity": (
                "The Telegraph operates a digital subscription model with onboarding sequences for new "
                "subscribers, billing and renewal transactional emails, and paywall prompts. They send "
                "editorial newsletters across multiple topics (politics, sport, finance, lifestyle). "
                "Their subscription funnel includes free trial offers and conversion sequences. "
                "They have a subscriber referral scheme and gift subscriptions, pointing to promotional "
                "campaign activity. Multi-channel engagement includes push notifications and app-based messaging."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Steven", "last_name": "Moriarty",
            "job_title": "Group Head Of CRM & Insight",
            "domain": "crewclothing.co.uk", "company_name": "Crew Clothing Company", "market": "UK",
        },
        "company": {
            "domain": "crewclothing.co.uk", "company_name": "Crew Clothing Company",
            "vertical": "fashion retail",
            "esp_detected": "SparkPost", "esp_score": 75,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Crew Clothing Company is a well-established UK lifestyle fashion retailer with an estimated "
                "500-1,000 employees operating an omnichannel model combining physical stores and e-commerce. "
                "They generate a rich set of customer communication needs: transactional emails, promotional "
                "campaigns, loyalty programme messaging (Crew Rewards), and SMS outreach. "
                "They sit squarely within Brevo's ICP as a retail and e-commerce brand."
            ),
            "email_crm_activity": (
                "Crew Clothing shows strong multi-channel communication activity: email newsletter sign-up "
                "for new arrivals and promotions; transactional emails for order confirmations, dispatch, "
                "and returns; seasonal promotional campaigns; loyalty programme (Crew Rewards) with points "
                "balance updates, tier progression, and member-exclusive offers; SMS marketing opt-in "
                "visible at sign-up. Customer communication layer is well-developed for a mid-sized "
                "omnichannel retailer."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Brogan", "last_name": "Wilson",
            "job_title": "CRM Manager",
            "domain": "gleneagles.com", "company_name": "Gleneagles", "market": "UK",
        },
        "company": {
            "domain": "gleneagles.com", "company_name": "Gleneagles",
            "vertical": "luxury hospitality",
            "esp_detected": "Mimecast", "esp_score": 50,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Gleneagles is a world-renowned five-star luxury hotel, resort, and golf destination in "
                "Perthshire, Scotland (part of Ennismore/Accor). It operates fine dining, a spa, shooting "
                "and outdoor pursuits, and hosts major events including the Ryder Cup. Observable multi-channel "
                "customer communication layer spanning booking confirmations, pre- and post-stay lifecycle "
                "emails, a membership club (The Club at Gleneagles) with tiered communications, promotional "
                "newsletters, event marketing, and gift voucher campaigns."
            ),
            "email_crm_activity": (
                "Gleneagles: marketing newsletters and editorial content under 'The Edit' email sign-up; "
                "transactional emails for room, dining, spa, and golf bookings; pre-stay and post-stay "
                "lifecycle guest journey sequences; The Club at Gleneagles membership programme with tiered "
                "benefits and ongoing member communications; event and experience promotion campaigns; "
                "gift voucher transactional communications."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Bethany", "last_name": "Garrett",
            "job_title": "CRM Manager (Product)",
            "domain": "fresha.com", "company_name": "Fresha", "market": "UK",
        },
        "company": {
            "domain": "fresha.com", "company_name": "Fresha",
            "vertical": "beauty and wellness technology",
            "esp_detected": "Mandrill", "esp_score": 100,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": True,
            "account_fit_score": 5,
            "account_narrative": (
                "Fresha is a beauty and wellness marketplace SaaS platform with ~900-1,000 staff. "
                "Their business model involves high-volume transactional and marketing communications "
                "across both consumer and B2B audiences: appointment confirmations, reminders, promotional "
                "campaigns, onboarding sequences, and SMS messaging are all core to their product and "
                "operations. They operate in hospitality and wellness — a core Brevo ICP vertical. "
                "The combination of marketplace-scale transactional email, multi-channel messaging, "
                "CRM workflows for venue partners, and consumer lifecycle communications makes this "
                "a textbook high-value prospect."
            ),
            "email_crm_activity": (
                "Fresha operates a dual-sided marketplace with rich multi-channel communications on both "
                "sides. Consumer side: transactional emails (appointment confirmations, reminders, receipts), "
                "marketing communications promoting venues and offers. Partner/B2B side: onboarding sequences "
                "for new salon and spa partners, B2B nurture communications. Their platform includes "
                "built-in marketing tools for venue partners to send promotional campaigns. "
                "SMS appointment reminders are a core product feature. Loyalty and membership features "
                "are offered to end consumers through the platform."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Kate", "last_name": "Taylor",
            "job_title": "CRM & Loyalty Manager",
            "domain": "theinkeylist.com", "company_name": "The INKEY List", "market": "UK",
        },
        "company": {
            "domain": "theinkeylist.com", "company_name": "The INKEY List",
            "vertical": "beauty and skincare DTC",
            "esp_detected": "SendGrid", "esp_score": 75,
            "has_loyalty_program": False, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "The INKEY List is a scaling DTC e-commerce and beauty retail brand with ~100-200 employees. "
                "They operate a direct online store requiring transactional and marketing email infrastructure. "
                "Their newsletter sign-up, active social presence (Instagram, TikTok, YouTube), and "
                "multi-channel retail footprint indicate a meaningful customer communication layer. "
                "The DTC beauty sector is a core Brevo ICP vertical. Their B Corp certification suggests "
                "investment in brand-to-consumer relationship building."
            ),
            "email_crm_activity": (
                "The INKEY List: DTC e-commerce store with transactional emails (order confirmations, "
                "shipping, receipts); newsletter sign-up with active promotional and marketing email campaigns; "
                "customer lifecycle sequences (post-purchase education, replenishment reminders, product "
                "recommendations); retail through third-party partners (Sephora, Boots, ASOS). "
                "No direct evidence of SMS programmes or loyalty app observed."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Mark", "last_name": "Lewis",
            "job_title": "CRM Loyalty Executive",
            "domain": "bulk.com", "company_name": "Bulk", "market": "UK",
        },
        "company": {
            "domain": "bulk.com", "company_name": "Bulk",
            "vertical": "health and nutrition DTC",
            "esp_detected": "SendGrid", "esp_score": 75,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Bulk is a high-volume DTC e-commerce brand in health and nutrition with ~600-800 employees. "
                "They operate across email, SMS, app, and loyalty channels generating substantial transactional "
                "and marketing communication volumes. They have a subscription product model, a loyalty "
                "programme (Bulk Rewards), and a large customer database built through digital acquisition — "
                "all hallmarks of a company with a mature and complex customer communication layer."
            ),
            "email_crm_activity": (
                "Bulk: newsletter sign-up with discount incentives (first-order discounts for email subscribers); "
                "transactional emails (order confirmations, dispatch, delivery updates); loyalty programme "
                "(Bulk Rewards) driving lifecycle and retention communications; subscription product (repeat "
                "delivery) implying onboarding and lifecycle sequences; mobile app with push notifications "
                "and likely SMS-based customer engagement."
            ),
        },
    },
    {
        "contact": {
            "first_name": "Isobel", "last_name": "L.",
            "job_title": "CRM & Digital Marketing Manager",
            "domain": "scottdunn.com", "company_name": "Scott Dunn", "market": "UK",
        },
        "company": {
            "domain": "scottdunn.com", "company_name": "Scott Dunn",
            "vertical": "luxury travel",
            "esp_detected": "Amazon SES", "esp_score": 75,
            "has_loyalty_program": True, "needs_cdp": True, "has_wallet": False,
            "account_fit_score": 5,
            "account_narrative": (
                "Scott Dunn is a high-end luxury travel company specialising in bespoke holidays, private "
                "villas, ski chalets, safaris, and tailor-made itineraries for affluent travellers. "
                "With ~500-700 staff they serve a high-value audience across multiple geographies, making "
                "segmentation, personalisation, and lifecycle marketing key priorities. They have a membership "
                "scheme (Scott Dunn Discerning Traveller), a referral programme, and a multinational presence."
            ),
            "email_crm_activity": (
                "Scott Dunn: newsletter sign-up for travel inspiration and exclusive offers; transactional "
                "emails for booking confirmations, itinerary details, pre-departure information, and post-trip "
                "follow-ups; customer lifecycle and re-engagement sequences for repeat bookings; "
                "Scott Dunn Discerning Traveller membership scheme communications; "
                "Invite a Friend referral programme; segmented localised messaging across UK, US, Asia-Pacific."
            ),
        },
    },
]

SYSTEM_PROMPT = (
    "You are a B2B copywriter. Output ONLY the raw JSON object requested. "
    "No reasoning, no analysis, no markdown fences, no preamble. "
    "Start your response with { and end with }."
)


async def generate(client: anthropic.AsyncAnthropic, lead: dict) -> dict:
    contact = lead["contact"]
    company = lead["company"]
    resource = select_resource(company)
    prompt = _build_content_prompt(contact, company, resource)

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    content = json.loads(raw)
    return {
        "contact": contact,
        "company": company,
        "resource": resource,
        "content": content,
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
    }


async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.AsyncAnthropic(api_key=api_key)
    print(f"Running {len(LEADS)} contacts in parallel...")

    results = await asyncio.gather(*[generate(client, lead) for lead in LEADS])

    output_path = os.path.join(os.path.dirname(__file__), "..", "output_sequences.csv")
    fieldnames = [
        "company_name", "first_name", "last_name", "job_title",
        "domain", "market", "vertical", "esp_detected",
        "has_loyalty_program", "has_wallet", "needs_cdp",
        "resource_selected",
        "subject_line_1", "email_1_body",
        "linkedin_connection_note", "linkedin_message_1",
        "subject_line_2", "email_2_body",
        "subject_line_3", "email_3_body",
        "linkedin_message_2",
        "subject_line_4", "email_4_body",
    ]

    total_in = sum(r["tokens_in"] for r in results)
    total_out = sum(r["tokens_out"] for r in results)
    cost = total_in * 1.50 / 1_000_000 + total_out * 7.50 / 1_000_000

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            c = r["content"]
            writer.writerow({
                "company_name":          r["company"]["company_name"],
                "first_name":            r["contact"]["first_name"],
                "last_name":             r["contact"]["last_name"],
                "job_title":             r["contact"]["job_title"],
                "domain":                r["company"]["domain"],
                "market":                r["contact"]["market"],
                "vertical":              r["company"]["vertical"],
                "esp_detected":          r["company"].get("esp_detected") or "",
                "has_loyalty_program":   r["company"]["has_loyalty_program"],
                "has_wallet":            r["company"]["has_wallet"],
                "needs_cdp":             r["company"]["needs_cdp"],
                "resource_selected":     r["resource"]["id"],
                "subject_line_1":        c["subject_line_1"],
                "email_1_body":          "\n\n".join([c["email_1_paragraph_1"], c["email_1_paragraph_2"], c["email_1_paragraph_3"]]),
                "linkedin_connection_note": c["linkedin_connection_note"],
                "linkedin_message_1":    c["linkedin_message_1"],
                "subject_line_2":        c["subject_line_2"],
                "email_2_body":          "\n\n".join([c["email_2_paragraph_1"], c["email_2_paragraph_2"]]),
                "subject_line_3":        c["subject_line_3"],
                "email_3_body":          "\n\n".join([c["email_3_paragraph_1"], c["email_3_paragraph_2"]]),
                "linkedin_message_2":    c["linkedin_message_2"],
                "subject_line_4":        c["subject_line_4"],
                "email_4_body":          "\n\n".join([c["email_4_paragraph_1"], c["email_4_paragraph_2"]]),
            })

    print(f"Done — {len(results)} rows written to output_sequences.csv")
    print(f"Tokens: {total_in:,} in / {total_out:,} out | Estimated cost: ${cost:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
