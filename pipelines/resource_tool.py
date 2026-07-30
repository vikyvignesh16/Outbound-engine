"""
Brevo resource catalogue for outbound content generation.

Source: data/Content_List_with_Outreach_Metrics_FINAL.numbers (241 ungated
resources — no gating, no form-fill required — each with a real, specific
outreach hook carrying an actual metric, and a real Brevo product/service tag
list). Replaces the earlier 16-entry hand-authored gated catalogue.

Resources are pre-filtered in Python via shortlist_resources() before being
injected into the prompt (by market-language, industry, signal, and archetype
fit) rather than dumping the full catalogue into every request — at this
scale that would be a large, costly injection on every single generation call.
"""

from typing import Any

RESOURCES: list[dict[str, Any]] = [   {   'id': 'involve-me-case-study-de',
        'company': 'Involve.me',
        'title': '(DE) One Pager: Involve.me - Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/DE-Involveme-case-study',
        'key_metrics': 'Involve.me lifted upsell purchases 8.7% and cut cancellations 6% by using '
                       "Brevo's behavior-triggered Email API sequences and personalized onboarding "
                       'flows — proof that automation drives real SaaS retention gains.',
        'context': 'This one-pager highlights how involve.me successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action",
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Marketing Automation',
                                   'Email API',
                                   'Personalization',
                                   'Sales CRM'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist']},
    {   'id': 'swisscommerce-case-study-case-study-de',
        'company': 'SwissCommerce Case Study',
        'title': '(DE) One Pager: SwissCommerce Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/DE-SwissCommerce-Case-Study',
        'key_metrics': "SwissCommerce centralized email marketing for 20 online shops on Brevo's "
                       'Multi-Account solution, hitting near-100% deliverability and 20-30% open '
                       'rates across every store — all while staying GDPR-compliant.',
        'context': 'This one-pager highlights how SwissCommerce successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Multi-Account Management',
                                   'Email Marketing',
                                   'Marketing Automation',
                                   'Messaging API',
                                   'Segmentation',
                                   'Deliverability'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Network', 'Consolidator', 'Email Specialist']},
    {   'id': 'vekoop-case-study-de',
        'company': 'Vekoop',
        'title': '(DE) One Pager: Vekoop - Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/DE-Vekoop-Case-Study',
        'key_metrics': 'Vegan retailer vekoop.de hit a 98.77% email deliverability rate right out '
                       "of the gate with Brevo's GDPR-compliant, drag-and-drop marketing platform "
                       '— no technical team required.',
        'context': 'This one-pager highlights how Vekoop successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Deliverability',
                                   'GDPR Compliance',
                                   'Drag-and-Drop Editor',
                                   'Integrations/Plugins'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': '10-push-notifications-ebook-ebook-fr',
        'company': '10 push notifications Ebook',
        'title': '10 push notifications Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-10-push-notifications-efficaces-fr-sls',
        'key_metrics': "One retargeting push notification got 20% of Oxybul's inactive subscribers "
                       'back to the site — this ebook breaks down 10 proven push-notification '
                       'playbooks (welcome flows, win-back campaigns, and more) from real Brevo '
                       'customers.',
        'context': "Through this guide, we'll explore why push notifications are beneficial to "
                   'business, how to implement them effectively, and which types of notifications '
                   'perform best.\n'
                   '\n'
                   'We reveal 10 types of push notifications that work, and how some companies '
                   'have successfully used them to achieve their marketing objectives.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Marketing Automation',
                                   'Customer Re-engagement',
                                   'Segmentation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': '10-push-notifications-ebook-ebook-de',
        'company': '10 push notifications Ebook',
        'title': '10 push notifications Ebook',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-10-arten-push-benachrichtigungen-2024-sls',
        'key_metrics': "One retargeting push notification got 20% of Oxybul's inactive subscribers "
                       'back to the site — this ebook breaks down 10 proven push-notification '
                       'playbooks (welcome flows, win-back campaigns, and more) from real Brevo '
                       'customers.',
        'context': "Through this guide, we'll explore why push notifications are beneficial to "
                   'business, how to implement them effectively, and which types of notifications '
                   'perform best.\n'
                   '\n'
                   'We reveal 10 types of push notifications that work, and how some companies '
                   'have successfully used them to achieve their marketing objectives.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Marketing Automation',
                                   'Customer Re-engagement',
                                   'Segmentation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': '10-push-notifications-ebook-ebook-en',
        'company': '10 push notifications Ebook',
        'title': '10 push notifications Ebook',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-10-push-notitications-en-sls',
        'key_metrics': "One retargeting push notification got 20% of Oxybul's inactive subscribers "
                       'back to the site — this ebook breaks down 10 proven push-notification '
                       'playbooks (welcome flows, win-back campaigns, and more) from real Brevo '
                       'customers.',
        'context': "Through this guide, we'll explore why push notifications are beneficial to "
                   'business, how to implement them effectively, and which types of notifications '
                   'perform best.\n'
                   '\n'
                   'We reveal 10 types of push notifications that work, and how some companies '
                   'have successfully used them to achieve their marketing objectives.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Marketing Automation',
                                   'Customer Re-engagement',
                                   'Segmentation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': '2026-marketing-orchestration-benchmark-ebook-en',
        'company': '2026 Marketing Orchestration Benchmark',
        'title': '2026 Marketing Orchestration Benchmark',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/K3SZRA8MUT',
        'key_metrics': "Brevo's 2026 benchmark (Jan-Dec 2025 data) shows how top-performing brands "
                       'protect email deliverability while orchestrating email, SMS, WhatsApp, '
                       'push, and mobile wallet campaigns into one seamless customer journey.',
        'context': 'This is also known as the annual email marketing industry benchmark. Asset '
                   'Name: 2026 Marketing Orchestration Benchmark\n'
                   'Asset Type: Gated Ebook / PDF Report\n'
                   'Target Audience: CMOs, VP Marketing, CRM Directors, Head of Lifecycle, RevOps\n'
                   'Market Segment: Mid-Market to Enterprise\n'
                   'Link to Asset: [Insert Link]\n'
                   '🎯 The "Elevator Pitch" (How to sell this asset)The era of relying on sheer '
                   'email volume is over. As brands send more emails, engagement drops and list '
                   'fatigue sets in. This benchmark analyzes 44+ billion emails across 175,000+ '
                   'businesses to prove that the only way to scale revenue is through Omnichannel '
                   'Orchestration. We show exactly how the Top 10% of brands protect their email '
                   'deliverability by shifting high-urgency and retention moments to specialist '
                   'channels like SMS, WhatsApp, Push, and Mobile Wallet to stop "channel '
                   'pile-up."\n'
                   '🔑 Key Search Tags (For internal discovery)benchmark 2026 email KPIs open rate '
                   'CTR unsubscribe rate deliverability omnichannel SMS WhatsApp Push '
                   'Notifications Mobile Wallet customer journey lead scoring RFM predictive '
                   'channel pile-up marketing pressure maturity model\n'
                   '📊 Master Summary & Key Findings to Share with ProspectsUse these data points '
                   'in your outreach emails or LinkedIn messages.\n'
                   '• Email Foundation:\xa0The global average open rate sits at\xa020.73%\xa0with '
                   'a\xa02.27% CTR. However, the Top 10% of senders achieve\xa044.02% Opens\xa0'
                   'and\xa05.22% CTR\xa0by running strict engagement-based segmentation.\n'
                   '• The Cost of Volume:\xa0High-volume senders (>1M emails/year) see CTRs drop '
                   'to\xa01.54%. The biggest risk is "silent disengagement"—when subscribers stop '
                   'opening without unsubscribing.\n'
                   '• SMS for Urgency:\xa0SMS volume is highly seasonal, peaking at\xa045.6M sends '
                   "in November. Top performers don't use SMS as a second email list; they use it "
                   'strictly for time-sensitive, high-intent moments (the "4-Hour Rule").\n'
                   '• WhatsApp for Service & Conversion:\xa0WhatsApp is expanding rapidly as an '
                   'intent-response channel, absorbing transactional pressure and driving two-way '
                   'conversations, especially in "WhatsApp-first" economies like India and LATAM.\n'
                   '• Push & Wallet for Habit & Retention:\xa0Push stays consistently active '
                   'year-round (88.7B notifications in 2025) as a real-time engager. Mobile Wallet '
                   'is the ultimate loyalty driver, growing\xa0+43% YoY\xa0with\xa043.97M active '
                   'passes\xa0by the end of 2025, allowing brands to bypass the crowded inbox '
                   'entirely.\n'
                   '🛠️ The 5-Level Omnichannel Maturity PlaybookThis report includes a diagnostic '
                   'framework. Use this to help prospects identify where they are stuck and how '
                   'Brevo can level them up.\n'
                   '1. Level 1 (Foundation):\xa0Single channel (Email). Risk of inbox fatigue.\xa0'
                   'Next move: Activate one complementary channel (like SMS for abandoned carts).\n'
                   '2. Level 2 (Exploration):\xa0Dual channel. Assigning urgency to SMS and depth '
                   'to Email.\xa0Next move: Integrate the data so channels stop operating in '
                   'silos.\n'
                   '3. Level 3 (Integration):\xa0The Unified Data Foundation. Moving from static '
                   'lists to dynamic, behavioral cohorts (e.g., "Clicked in the last 30 days, no '
                   'purchase").\n'
                   '4. Level 4 (Advanced):\xa0Real-Time Orchestration. Replacing calendar sends '
                   'with event-driven workflows and cross-channel fallback logic based on live '
                   'intent signals.\n'
                   '5. Level 5 (Optimization):\xa0Predictive precision. Using AI to scale '
                   'decisions, enforcing strict cross-channel governance, and measuring true '
                   'incrementality (not just clicks).\n'
                   '🗣️ Expert Voices Featured (Agencies & Partners)The report is validated by '
                   'elite CRM agencies. Mention them if a prospect asks for best practices.\n'
                   '• Will Pearson\xa0(Scalero)\n'
                   '• Yohann Delahaye\xa0(Avanci)\n'
                   '• Sabrina Villepinte\xa0(Elevate Agency)\n'
                   '• Hervé Malinge\xa0(Yuri & Neil)\n'
                   '• Guillaume Demonsant\xa0(Dentsu)',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Marketing',
                                   'WhatsApp Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet Marketing',
                                   'Marketing Automation',
                                   'Omnichannel Orchestration'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': '2026-marketing-orchestration-benchmark-ebook-fr',
        'company': '2026 Marketing Orchestration Benchmark',
        'title': '2026 Marketing Orchestration Benchmark',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/K3SZRA8MUT',
        'key_metrics': "Brevo's 2026 benchmark (Jan-Dec 2025 data) shows how top-performing brands "
                       'protect email deliverability while orchestrating email, SMS, WhatsApp, '
                       'push, and mobile wallet campaigns into one seamless customer journey.',
        'context': 'This is also known as the annual email marketing industry benchmark. Asset '
                   'Name: 2026 Marketing Orchestration Benchmark\n'
                   'Asset Type: Gated Ebook / PDF Report\n'
                   'Target Audience: CMOs, VP Marketing, CRM Directors, Head of Lifecycle, RevOps\n'
                   'Market Segment: Mid-Market to Enterprise\n'
                   'Link to Asset: [Insert Link]\n'
                   '🎯 The "Elevator Pitch" (How to sell this asset)The era of relying on sheer '
                   'email volume is over. As brands send more emails, engagement drops and list '
                   'fatigue sets in. This benchmark analyzes 44+ billion emails across 175,000+ '
                   'businesses to prove that the only way to scale revenue is through Omnichannel '
                   'Orchestration. We show exactly how the Top 10% of brands protect their email '
                   'deliverability by shifting high-urgency and retention moments to specialist '
                   'channels like SMS, WhatsApp, Push, and Mobile Wallet to stop "channel '
                   'pile-up."\n'
                   '🔑 Key Search Tags (For internal discovery)benchmark 2026 email KPIs open rate '
                   'CTR unsubscribe rate deliverability omnichannel SMS WhatsApp Push '
                   'Notifications Mobile Wallet customer journey lead scoring RFM predictive '
                   'channel pile-up marketing pressure maturity model\n'
                   '📊 Master Summary & Key Findings to Share with ProspectsUse these data points '
                   'in your outreach emails or LinkedIn messages.\n'
                   '• Email Foundation:\xa0The global average open rate sits at\xa020.73%\xa0with '
                   'a\xa02.27% CTR. However, the Top 10% of senders achieve\xa044.02% Opens\xa0'
                   'and\xa05.22% CTR\xa0by running strict engagement-based segmentation.\n'
                   '• The Cost of Volume:\xa0High-volume senders (>1M emails/year) see CTRs drop '
                   'to\xa01.54%. The biggest risk is "silent disengagement"—when subscribers stop '
                   'opening without unsubscribing.\n'
                   '• SMS for Urgency:\xa0SMS volume is highly seasonal, peaking at\xa045.6M sends '
                   "in November. Top performers don't use SMS as a second email list; they use it "
                   'strictly for time-sensitive, high-intent moments (the "4-Hour Rule").\n'
                   '• WhatsApp for Service & Conversion:\xa0WhatsApp is expanding rapidly as an '
                   'intent-response channel, absorbing transactional pressure and driving two-way '
                   'conversations, especially in "WhatsApp-first" economies like India and LATAM.\n'
                   '• Push & Wallet for Habit & Retention:\xa0Push stays consistently active '
                   'year-round (88.7B notifications in 2025) as a real-time engager. Mobile Wallet '
                   'is the ultimate loyalty driver, growing\xa0+43% YoY\xa0with\xa043.97M active '
                   'passes\xa0by the end of 2025, allowing brands to bypass the crowded inbox '
                   'entirely.\n'
                   '🛠️ The 5-Level Omnichannel Maturity PlaybookThis report includes a diagnostic '
                   'framework. Use this to help prospects identify where they are stuck and how '
                   'Brevo can level them up.\n'
                   '1. Level 1 (Foundation):\xa0Single channel (Email). Risk of inbox fatigue.\xa0'
                   'Next move: Activate one complementary channel (like SMS for abandoned carts).\n'
                   '2. Level 2 (Exploration):\xa0Dual channel. Assigning urgency to SMS and depth '
                   'to Email.\xa0Next move: Integrate the data so channels stop operating in '
                   'silos.\n'
                   '3. Level 3 (Integration):\xa0The Unified Data Foundation. Moving from static '
                   'lists to dynamic, behavioral cohorts (e.g., "Clicked in the last 30 days, no '
                   'purchase").\n'
                   '4. Level 4 (Advanced):\xa0Real-Time Orchestration. Replacing calendar sends '
                   'with event-driven workflows and cross-channel fallback logic based on live '
                   'intent signals.\n'
                   '5. Level 5 (Optimization):\xa0Predictive precision. Using AI to scale '
                   'decisions, enforcing strict cross-channel governance, and measuring true '
                   'incrementality (not just clicks).\n'
                   '🗣️ Expert Voices Featured (Agencies & Partners)The report is validated by '
                   'elite CRM agencies. Mention them if a prospect asks for best practices.\n'
                   '• Will Pearson\xa0(Scalero)\n'
                   '• Yohann Delahaye\xa0(Avanci)\n'
                   '• Sabrina Villepinte\xa0(Elevate Agency)\n'
                   '• Hervé Malinge\xa0(Yuri & Neil)\n'
                   '• Guillaume Demonsant\xa0(Dentsu)',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Marketing',
                                   'WhatsApp Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet Marketing',
                                   'Marketing Automation',
                                   'Omnichannel Orchestration'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': '2026-marketing-orchestration-benchmark-ebook-de',
        'company': '2026 Marketing Orchestration Benchmark',
        'title': '2026 Marketing Orchestration Benchmark',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/BgA6uSUPWZ',
        'key_metrics': "Brevo's 2026 benchmark (Jan-Dec 2025 data) shows how top-performing brands "
                       'protect email deliverability while orchestrating email, SMS, WhatsApp, '
                       'push, and mobile wallet campaigns into one seamless customer journey.',
        'context': 'This is also known as the annual email marketing industry benchmark. Asset '
                   'Name: 2026 Marketing Orchestration Benchmark\n'
                   'Asset Type: Gated Ebook / PDF Report\n'
                   'Target Audience: CMOs, VP Marketing, CRM Directors, Head of Lifecycle, RevOps\n'
                   'Market Segment: Mid-Market to Enterprise\n'
                   'Link to Asset: [Insert Link]\n'
                   '🎯 The "Elevator Pitch" (How to sell this asset)The era of relying on sheer '
                   'email volume is over. As brands send more emails, engagement drops and list '
                   'fatigue sets in. This benchmark analyzes 44+ billion emails across 175,000+ '
                   'businesses to prove that the only way to scale revenue is through Omnichannel '
                   'Orchestration. We show exactly how the Top 10% of brands protect their email '
                   'deliverability by shifting high-urgency and retention moments to specialist '
                   'channels like SMS, WhatsApp, Push, and Mobile Wallet to stop "channel '
                   'pile-up."\n'
                   '🔑 Key Search Tags (For internal discovery)benchmark 2026 email KPIs open rate '
                   'CTR unsubscribe rate deliverability omnichannel SMS WhatsApp Push '
                   'Notifications Mobile Wallet customer journey lead scoring RFM predictive '
                   'channel pile-up marketing pressure maturity model\n'
                   '📊 Master Summary & Key Findings to Share with ProspectsUse these data points '
                   'in your outreach emails or LinkedIn messages.\n'
                   '• Email Foundation:\xa0The global average open rate sits at\xa020.73%\xa0with '
                   'a\xa02.27% CTR. However, the Top 10% of senders achieve\xa044.02% Opens\xa0'
                   'and\xa05.22% CTR\xa0by running strict engagement-based segmentation.\n'
                   '• The Cost of Volume:\xa0High-volume senders (>1M emails/year) see CTRs drop '
                   'to\xa01.54%. The biggest risk is "silent disengagement"—when subscribers stop '
                   'opening without unsubscribing.\n'
                   '• SMS for Urgency:\xa0SMS volume is highly seasonal, peaking at\xa045.6M sends '
                   "in November. Top performers don't use SMS as a second email list; they use it "
                   'strictly for time-sensitive, high-intent moments (the "4-Hour Rule").\n'
                   '• WhatsApp for Service & Conversion:\xa0WhatsApp is expanding rapidly as an '
                   'intent-response channel, absorbing transactional pressure and driving two-way '
                   'conversations, especially in "WhatsApp-first" economies like India and LATAM.\n'
                   '• Push & Wallet for Habit & Retention:\xa0Push stays consistently active '
                   'year-round (88.7B notifications in 2025) as a real-time engager. Mobile Wallet '
                   'is the ultimate loyalty driver, growing\xa0+43% YoY\xa0with\xa043.97M active '
                   'passes\xa0by the end of 2025, allowing brands to bypass the crowded inbox '
                   'entirely.\n'
                   '🛠️ The 5-Level Omnichannel Maturity PlaybookThis report includes a diagnostic '
                   'framework. Use this to help prospects identify where they are stuck and how '
                   'Brevo can level them up.\n'
                   '1. Level 1 (Foundation):\xa0Single channel (Email). Risk of inbox fatigue.\xa0'
                   'Next move: Activate one complementary channel (like SMS for abandoned carts).\n'
                   '2. Level 2 (Exploration):\xa0Dual channel. Assigning urgency to SMS and depth '
                   'to Email.\xa0Next move: Integrate the data so channels stop operating in '
                   'silos.\n'
                   '3. Level 3 (Integration):\xa0The Unified Data Foundation. Moving from static '
                   'lists to dynamic, behavioral cohorts (e.g., "Clicked in the last 30 days, no '
                   'purchase").\n'
                   '4. Level 4 (Advanced):\xa0Real-Time Orchestration. Replacing calendar sends '
                   'with event-driven workflows and cross-channel fallback logic based on live '
                   'intent signals.\n'
                   '5. Level 5 (Optimization):\xa0Predictive precision. Using AI to scale '
                   'decisions, enforcing strict cross-channel governance, and measuring true '
                   'incrementality (not just clicks).\n'
                   '🗣️ Expert Voices Featured (Agencies & Partners)The report is validated by '
                   'elite CRM agencies. Mention them if a prospect asks for best practices.\n'
                   '• Will Pearson\xa0(Scalero)\n'
                   '• Yohann Delahaye\xa0(Avanci)\n'
                   '• Sabrina Villepinte\xa0(Elevate Agency)\n'
                   '• Hervé Malinge\xa0(Yuri & Neil)\n'
                   '• Guillaume Demonsant\xa0(Dentsu)',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Marketing',
                                   'WhatsApp Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet Marketing',
                                   'Marketing Automation',
                                   'Omnichannel Orchestration'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': '5-b2c-strategies-for-business-growth-ebook-en',
        'company': '5 B2C Strategies for Business Growth',
        'title': '5 B2C Strategies for Business Growth',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/5-B2C-Strategies-for-Business-Growth-sls',
        'key_metrics': '5 real B2C brands share exactly how they used Brevo to boost engagement '
                       'and multiply revenue — a fast read on which growth levers (automation, '
                       'segmentation, personalization) actually moved the needle.',
        'context': 'This ebook showcases Brevo’s successful CRM strategies that have driven growth '
                   'for real-world clients without naming them. There are five key strategies: '
                   'personalizing customer journeys, making data-driven decisions, unifying '
                   'customer data, boosting customer lifetime value, and leveraging a '
                   'multi-channel approach. Each section includes case studies and practical '
                   'examples, demonstrating how these strategies were implemented to solve client '
                   'challenges and achieve measurable results.\xa0\n'
                   'It can be used to communicate the impact of Brevo’s solutions to potential and '
                   'existing clients',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'B2C Marketing',
                                   'Customer Engagement',
                                   'Revenue Growth'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': '5-b2c-strategies-for-business-growth-ebook-de',
        'company': '5 B2C Strategies for Business Growth',
        'title': '5 B2C Strategies for Business Growth',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/DE-5-B2C-Strategies-for-Business-Growth-sls',
        'key_metrics': '5 real B2C brands share exactly how they used Brevo to boost engagement '
                       'and multiply revenue — a fast read on which growth levers (automation, '
                       'segmentation, personalization) actually moved the needle.',
        'context': 'This ebook showcases Brevo’s successful CRM strategies that have driven growth '
                   'for real-world clients without naming them. There are five key strategies: '
                   'personalizing customer journeys, making data-driven decisions, unifying '
                   'customer data, boosting customer lifetime value, and leveraging a '
                   'multi-channel approach. Each section includes case studies and practical '
                   'examples, demonstrating how these strategies were implemented to solve client '
                   'challenges and achieve measurable results.\xa0\n'
                   'It can be used to communicate the impact of Brevo’s solutions to potential and '
                   'existing clients',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'B2C Marketing',
                                   'Customer Engagement',
                                   'Revenue Growth'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': '5-b2c-strategies-for-business-growth-ebook-fr',
        'company': '5 B2C Strategies for Business Growth',
        'title': '5 B2C Strategies for Business Growth',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/FR-5-B2C-Strategies-for-Business-Growth-sls',
        'key_metrics': '5 real B2C brands share exactly how they used Brevo to boost engagement '
                       'and multiply revenue — a fast read on which growth levers (automation, '
                       'segmentation, personalization) actually moved the needle.',
        'context': 'This ebook showcases Brevo’s successful CRM strategies that have driven growth '
                   'for real-world clients without naming them. There are five key strategies: '
                   'personalizing customer journeys, making data-driven decisions, unifying '
                   'customer data, boosting customer lifetime value, and leveraging a '
                   'multi-channel approach. Each section includes case studies and practical '
                   'examples, demonstrating how these strategies were implemented to solve client '
                   'challenges and achieve measurable results.\xa0\n'
                   'It can be used to communicate the impact of Brevo’s solutions to potential and '
                   'existing clients',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'B2C Marketing',
                                   'Customer Engagement',
                                   'Revenue Growth'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': '5-crm-strategies-depending-your-business-goal-ebook-fr',
        'company': '5 CRM Strategies depending your business goal',
        'title': '5 CRM Strategies depending your business goal',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/5-strategies-CRM-selon-objectif-sls',
        'key_metrics': '5 CRM strategies mapped directly to specific business goals — acquisition, '
                       'retention, upsell, or reactivation — so teams can pick the exact playbook '
                       "that fits what they're trying to achieve right now.",
        'context': 'This ebook presents five actionable CRM strategies to help you achieve key '
                   'business goals: acquiring new contacts through optimized forms, boosting '
                   'customer engagement with personalized email automation, reducing churn with a '
                   'Customer Data Platform (CDP) and automation, increasing conversion rates via '
                   'transactional messaging, and maximizing customer lifetime value (CLTV) through '
                   'wallet marketing. Each chapter features real-world examples from brands like '
                   'Burda Style, Alltricks, Trusted Shops, Doctolib, Courir, and Corsair, and '
                   'demonstrates how Brevo empowers companies to deploy innovative CRM solutions '
                   'for growth and loyalty.\n'
                   '👉 A must-read for anyone looking to evolve their CRM practices and get '
                   'inspired by concrete use cases!',
        'pain_points': '',
        'brevo_features_tags': [   'CRM',
                                   'Marketing Automation',
                                   'Customer Segmentation',
                                   'Sales CRM'],
        'best_for_verticals': ['retail', 'media_publishing', 'hospitality', 'tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '5-use-cases-to-convert-and-retain-your-customers-through-seg',
        'company': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'title': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-segmentation-retail-marketing-fr-sls',
        'key_metrics': 'See how pairing a single behavior trigger (product page visit + email '
                       'open) launches a hyper-targeted discount offer — this guide details 5 '
                       'segmentation use cases, backed by McKinsey research, for converting and '
                       'retaining retail customers.',
        'context': 'This ebook shows you the best practices for segmenting your audience and '
                   'personalizing your campaigns to maximize their impact.',
        'pain_points': '',
        'brevo_features_tags': [   'Segmentation',
                                   'Marketing Automation',
                                   'Email Marketing',
                                   'Customer Retention',
                                   'Retail Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '5-use-cases-to-convert-and-retain-your-customers-through-seg-2',
        'company': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'title': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-segmentation-retail-marketing-en-sls',
        'key_metrics': 'See how pairing a single behavior trigger (product page visit + email '
                       'open) launches a hyper-targeted discount offer — this guide details 5 '
                       'segmentation use cases, backed by McKinsey research, for converting and '
                       'retaining retail customers.',
        'context': 'This ebook shows you the best practices for segmenting your audience and '
                   'personalizing your campaigns to maximize their impact.',
        'pain_points': '',
        'brevo_features_tags': [   'Segmentation',
                                   'Marketing Automation',
                                   'Email Marketing',
                                   'Customer Retention',
                                   'Retail Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '5-use-cases-to-convert-and-retain-your-customers-through-seg-3',
        'company': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'title': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-segmentation-retail-marketing-de-sls',
        'key_metrics': 'See how pairing a single behavior trigger (product page visit + email '
                       'open) launches a hyper-targeted discount offer — this guide details 5 '
                       'segmentation use cases, backed by McKinsey research, for converting and '
                       'retaining retail customers.',
        'context': 'This ebook shows you the best practices for segmenting your audience and '
                   'personalizing your campaigns to maximize their impact.',
        'pain_points': '',
        'brevo_features_tags': [   'Segmentation',
                                   'Marketing Automation',
                                   'Email Marketing',
                                   'Customer Retention',
                                   'Retail Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '5-use-cases-to-convert-and-retain-your-customers-through-seg-4',
        'company': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'title': '5 Use Cases to Convert and Retain Your Customers Through Segmentation',
        'type': 'ebook',
        'language': 'ES',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-segmentation-retail-es-sls',
        'key_metrics': 'See how pairing a single behavior trigger (product page visit + email '
                       'open) launches a hyper-targeted discount offer — this guide details 5 '
                       'segmentation use cases, backed by McKinsey research, for converting and '
                       'retaining retail customers.',
        'context': 'This ebook shows you the best practices for segmenting your audience and '
                   'personalizing your campaigns to maximize their impact.',
        'pain_points': '',
        'brevo_features_tags': [   'Segmentation',
                                   'Marketing Automation',
                                   'Email Marketing',
                                   'Customer Retention',
                                   'Retail Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '5-ways-to-improve-ecommerce-kpis-ebook-en',
        'company': '5 Ways to Improve Ecommerce KPIs',
        'title': '5 Ways to Improve Ecommerce KPIs',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Ebook-improve-ecommerce-KPI-sls',
        'key_metrics': 'A tactical playbook for moving 5 core ecommerce KPIs — customer loyalty, '
                       'cross-sell revenue, conversions, retention, and cart abandonment — with '
                       'specific plays for each stage of the funnel.',
        'context': 'As the title suggests, this resource (ebook) targets e-commerce KPIs (Loyalty, '
                   'cross-sell, retention, conversions, -cart abandonment) and how brands can '
                   'improve targets. However it also touches on other KPIs that also benefit from '
                   'the strategies mentioned. Products mentioned: Loyalty and multi-channel, '
                   'e-commerce dash and Potions, Live Chat Chat/Chat Bot/ Push notifications)',
        'pain_points': '',
        'brevo_features_tags': [   'Ecommerce',
                                   'Marketing Automation',
                                   'Cross-sell',
                                   'Cart Abandonment Recovery',
                                   'Customer Retention',
                                   'Conversion Optimization'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '7-omnichannel-marketing-tactics-to-strengthen-the-commitment',
        'company': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of '
                   'your customers',
        'title': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of your '
                 'customers',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-omnichannel-retail-marketing-fr-sls',
        'key_metrics': 'A Retail Excellence playbook: 7 omnichannel tactics top retailers use to '
                       'deepen customer loyalty and commitment by weaving email, SMS, and in-store '
                       'touchpoints into one seamless brand experience.',
        'context': 'This ebook provides an introduction to best practices for building customer '
                   'loyalty and maximizing results through channel integration, campaign '
                   'automation, and data centralization.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'Customer Loyalty',
                                   'Retail Marketing',
                                   'Email Marketing',
                                   'SMS Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '7-omnichannel-marketing-tactics-to-strengthen-the-commitment-2',
        'company': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of '
                   'your customers',
        'title': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of your '
                 'customers',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-omnichannel-retail-marketing-en-sls',
        'key_metrics': 'A Retail Excellence playbook: 7 omnichannel tactics top retailers use to '
                       'deepen customer loyalty and commitment by weaving email, SMS, and in-store '
                       'touchpoints into one seamless brand experience.',
        'context': 'This ebook provides an introduction to best practices for building customer '
                   'loyalty and maximizing results through channel integration, campaign '
                   'automation, and data centralization.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'Customer Loyalty',
                                   'Retail Marketing',
                                   'Email Marketing',
                                   'SMS Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '7-omnichannel-marketing-tactics-to-strengthen-the-commitment-3',
        'company': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of '
                   'your customers',
        'title': '7 omnichannel marketing tactics to strengthen the commitment and loyalty of your '
                 'customers',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-omnichannel-retail-marketing-de-sls',
        'key_metrics': 'A Retail Excellence playbook: 7 omnichannel tactics top retailers use to '
                       'deepen customer loyalty and commitment by weaving email, SMS, and in-store '
                       'touchpoints into one seamless brand experience.',
        'context': 'This ebook provides an introduction to best practices for building customer '
                   'loyalty and maximizing results through channel integration, campaign '
                   'automation, and data centralization.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'Customer Loyalty',
                                   'Retail Marketing',
                                   'Email Marketing',
                                   'SMS Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '8-pop-up-notifications-ebook-ebook-fr',
        'company': '8 pop-up notifications Ebook',
        'title': '8 pop-up notifications Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-8-popup-efficaces-fr-sls',
        'key_metrics': "Aquarelle's responsive '€5 off your first order' pop-up hit a 12% "
                       'click-through rate across desktop and mobile — this ebook shows 8 proven '
                       'pop-up formats for activating and converting site visitors.',
        'context': "In this ebook, you'll discover why pop-ups are good for your business, how to "
                   'implement them effectively and concrete examples of how to maximise their '
                   'effectiveness.',
        'pain_points': '',
        'brevo_features_tags': [   'Pop-up Marketing',
                                   'On-site Messaging',
                                   'Conversion Rate Optimization',
                                   'Cart Abandonment',
                                   'Lead Generation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': '8-pop-up-notifications-ebook-ebook-de',
        'company': '8 pop-up notifications Ebook',
        'title': '8 pop-up notifications Ebook',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-8-pop-ups-2024-sls',
        'key_metrics': "Aquarelle's responsive '€5 off your first order' pop-up hit a 12% "
                       'click-through rate across desktop and mobile — this ebook shows 8 proven '
                       'pop-up formats for activating and converting site visitors.',
        'context': "In this ebook, you'll discover why pop-ups are good for your business, how to "
                   'implement them effectively and concrete examples of how to maximise their '
                   'effectiveness.',
        'pain_points': '',
        'brevo_features_tags': [   'Pop-up Marketing',
                                   'On-site Messaging',
                                   'Conversion Rate Optimization',
                                   'Cart Abandonment',
                                   'Lead Generation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': '8-pop-up-notifications-ebook-ebook-en',
        'company': '8 pop-up notifications Ebook',
        'title': '8 pop-up notifications Ebook',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-8-pop-up-en-sls',
        'key_metrics': "Aquarelle's responsive '€5 off your first order' pop-up hit a 12% "
                       'click-through rate across desktop and mobile — this ebook shows 8 proven '
                       'pop-up formats for activating and converting site visitors.',
        'context': "In this ebook, you'll discover why pop-ups are good for your business, how to "
                   'implement them effectively and concrete examples of how to maximise their '
                   'effectiveness.',
        'pain_points': '',
        'brevo_features_tags': [   'Pop-up Marketing',
                                   'On-site Messaging',
                                   'Conversion Rate Optimization',
                                   'Cart Abandonment',
                                   'Lead Generation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': '8-steps-to-creating-an-effective-loyalty-program-ebook-fr',
        'company': '8 steps to creating an effective loyalty program',
        'title': '8 steps to creating an effective loyalty program',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-8-etapes-programme-fidelite-fr-sls',
        'key_metrics': 'An 8-step blueprint for building a loyalty program that actually keeps '
                       'customers coming back — covering points structures, reward tiers, and the '
                       'communication cadence that keeps members engaged.',
        'context': 'This e-book explains the 8 key steps to creating an effective loyalty program '
                   'such as : Define program objectives, know your customer base, select the type '
                   'of loyalty program, determine rewards and benefits etc.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Marketing Automation',
                                   'Customer Retention',
                                   'Email Marketing',
                                   'Retail Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '8-steps-to-creating-an-effective-loyalty-program-ebook-de',
        'company': '8 steps to creating an effective loyalty program',
        'title': '8 steps to creating an effective loyalty program',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-8-schritte-treueprogramm-sls',
        'key_metrics': 'An 8-step blueprint for building a loyalty program that actually keeps '
                       'customers coming back — covering points structures, reward tiers, and the '
                       'communication cadence that keeps members engaged.',
        'context': 'This e-book explains the 8 key steps to creating an effective loyalty program '
                   'such as : Define program objectives, know your customer base, select the type '
                   'of loyalty program, determine rewards and benefits etc.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Marketing Automation',
                                   'Customer Retention',
                                   'Email Marketing',
                                   'Retail Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '8-steps-to-creating-an-effective-loyalty-program-ebook-en',
        'company': '8 steps to creating an effective loyalty program',
        'title': '8 steps to creating an effective loyalty program',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-8-steps-loyalty-en-sls',
        'key_metrics': 'An 8-step blueprint for building a loyalty program that actually keeps '
                       'customers coming back — covering points structures, reward tiers, and the '
                       'communication cadence that keeps members engaged.',
        'context': 'This e-book explains the 8 key steps to creating an effective loyalty program '
                   'such as : Define program objectives, know your customer base, select the type '
                   'of loyalty program, determine rewards and benefits etc.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Marketing Automation',
                                   'Customer Retention',
                                   'Email Marketing',
                                   'Retail Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '9-cdp-use-cases-for-retailers-ebook-en',
        'company': '9 CDP Use Cases for Retailers',
        'title': '9 CDP Use Cases for Retailers',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/CDP-use-cases-retail-sls',
        'key_metrics': '9 ways retailers use a Customer Data Platform to centralize and sync '
                       'first- and second-party data — deploying real-time customer segments in '
                       'minutes and boosting campaign ROI without relying on IT.',
        'context': 'Master summary: This presentation outlines 9 specific Customer Data Platform '
                   '(CDP) use cases for retail brands. It explains how Brevo CDP centralizes '
                   'scattered data into a single customer view to power actionable intelligence, '
                   'targeted segmentation, and cross-channel personalization.\n'
                   'Best use / When to share: Share during the Consideration or Decision stages '
                   'with retail and e-commerce leaders (CMOs, Head of E-commerce, Data/CRM teams). '
                   'It directly addresses the pain points of scattered data silos, ineffective '
                   'segmentation, and the inability to quickly analyze customer behavior. It '
                   'proves the value of investing in a CDP to improve Average Cart Value and '
                   'Customer Lifetime Value (CLTV).\n'
                   'Key takeaways:\n'
                   '• Single Customer View: Unifies data from CRMs, POS systems, and apps into '
                   '360-degree profiles.\n'
                   '• Advanced Segmentation: Uses RFM (Recency, Frequency, Monetary) scoring to '
                   'identify high-value vs. dormant customers for precise reactivation campaigns.\n'
                   '• Product Personalization: Drives cross-selling and up-selling by recommending '
                   'products based on browsing behavior, purchase history, and cohort trends.\n'
                   '• Omnichannel Orchestration: Maps the customer journey across online and '
                   'in-store touchpoints to optimize the best converting channels (Email, SMS, '
                   'Push, Ads).\n'
                   '• Predictive Analytics: Features built-in analytics dashboards (powered by '
                   'Looker Studio) to forecast inventory demand, analyze seasonal buying trends, '
                   'and automate feedback surveys (includes success metrics from KFC France and '
                   'Yumpingo).\n'
                   'Search keywords: CDP, Customer Data Platform, retail, e-commerce, single '
                   'customer view, 360 profile, audience segmentation, RFM scoring, product '
                   'recommendations, cross-sell, upsell, omnichannel orchestration, CLTV, '
                   'predictive analytics, Looker Studio, data synchronization, presentation, deck, '
                   'slides, KFC France, Yumpingo\n'
                   'Notes & Status: Content is targeted explicitly at the Retail and E-commerce '
                   'industries. No publication date is explicitly listed. Features customer quotes '
                   'from KFC France and Yumpingo. Validated for use in Enterprise sales motions '
                   'regarding the Brevo CDP.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP (Customer Data Platform)',
                                   'Segmentation',
                                   'Data Integration',
                                   'Retail Marketing',
                                   'Marketing Automation'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': '9-cdp-use-cases-for-retailers-ebook-de',
        'company': '9 CDP Use Cases for Retailers',
        'title': '9 CDP Use Cases for Retailers',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/de-9-cdp-usecases-retail-sls',
        'key_metrics': '9 ways retailers use a Customer Data Platform to centralize and sync '
                       'first- and second-party data — deploying real-time customer segments in '
                       'minutes and boosting campaign ROI without relying on IT.',
        'context': 'Master summary: This presentation outlines 9 specific Customer Data Platform '
                   '(CDP) use cases for retail brands. It explains how Brevo CDP centralizes '
                   'scattered data into a single customer view to power actionable intelligence, '
                   'targeted segmentation, and cross-channel personalization.\n'
                   'Best use / When to share: Share during the Consideration or Decision stages '
                   'with retail and e-commerce leaders (CMOs, Head of E-commerce, Data/CRM teams). '
                   'It directly addresses the pain points of scattered data silos, ineffective '
                   'segmentation, and the inability to quickly analyze customer behavior. It '
                   'proves the value of investing in a CDP to improve Average Cart Value and '
                   'Customer Lifetime Value (CLTV).\n'
                   'Key takeaways:\n'
                   '• Single Customer View: Unifies data from CRMs, POS systems, and apps into '
                   '360-degree profiles.\n'
                   '• Advanced Segmentation: Uses RFM (Recency, Frequency, Monetary) scoring to '
                   'identify high-value vs. dormant customers for precise reactivation campaigns.\n'
                   '• Product Personalization: Drives cross-selling and up-selling by recommending '
                   'products based on browsing behavior, purchase history, and cohort trends.\n'
                   '• Omnichannel Orchestration: Maps the customer journey across online and '
                   'in-store touchpoints to optimize the best converting channels (Email, SMS, '
                   'Push, Ads).\n'
                   '• Predictive Analytics: Features built-in analytics dashboards (powered by '
                   'Looker Studio) to forecast inventory demand, analyze seasonal buying trends, '
                   'and automate feedback surveys (includes success metrics from KFC France and '
                   'Yumpingo).\n'
                   'Search keywords: CDP, Customer Data Platform, retail, e-commerce, single '
                   'customer view, 360 profile, audience segmentation, RFM scoring, product '
                   'recommendations, cross-sell, upsell, omnichannel orchestration, CLTV, '
                   'predictive analytics, Looker Studio, data synchronization, presentation, deck, '
                   'slides, KFC France, Yumpingo\n'
                   'Notes & Status: Content is targeted explicitly at the Retail and E-commerce '
                   'industries. No publication date is explicitly listed. Features customer quotes '
                   'from KFC France and Yumpingo. Validated for use in Enterprise sales motions '
                   'regarding the Brevo CDP.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP (Customer Data Platform)',
                                   'Segmentation',
                                   'Data Integration',
                                   'Retail Marketing',
                                   'Marketing Automation'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': '9-cdp-use-cases-for-retailers-ebook-fr',
        'company': '9 CDP Use Cases for Retailers',
        'title': '9 CDP Use Cases for Retailers',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/CDP-Use-Cases-Retailers-sls',
        'key_metrics': '9 ways retailers use a Customer Data Platform to centralize and sync '
                       'first- and second-party data — deploying real-time customer segments in '
                       'minutes and boosting campaign ROI without relying on IT.',
        'context': 'Master summary: This presentation outlines 9 specific Customer Data Platform '
                   '(CDP) use cases for retail brands. It explains how Brevo CDP centralizes '
                   'scattered data into a single customer view to power actionable intelligence, '
                   'targeted segmentation, and cross-channel personalization.\n'
                   'Best use / When to share: Share during the Consideration or Decision stages '
                   'with retail and e-commerce leaders (CMOs, Head of E-commerce, Data/CRM teams). '
                   'It directly addresses the pain points of scattered data silos, ineffective '
                   'segmentation, and the inability to quickly analyze customer behavior. It '
                   'proves the value of investing in a CDP to improve Average Cart Value and '
                   'Customer Lifetime Value (CLTV).\n'
                   'Key takeaways:\n'
                   '• Single Customer View: Unifies data from CRMs, POS systems, and apps into '
                   '360-degree profiles.\n'
                   '• Advanced Segmentation: Uses RFM (Recency, Frequency, Monetary) scoring to '
                   'identify high-value vs. dormant customers for precise reactivation campaigns.\n'
                   '• Product Personalization: Drives cross-selling and up-selling by recommending '
                   'products based on browsing behavior, purchase history, and cohort trends.\n'
                   '• Omnichannel Orchestration: Maps the customer journey across online and '
                   'in-store touchpoints to optimize the best converting channels (Email, SMS, '
                   'Push, Ads).\n'
                   '• Predictive Analytics: Features built-in analytics dashboards (powered by '
                   'Looker Studio) to forecast inventory demand, analyze seasonal buying trends, '
                   'and automate feedback surveys (includes success metrics from KFC France and '
                   'Yumpingo).\n'
                   'Search keywords: CDP, Customer Data Platform, retail, e-commerce, single '
                   'customer view, 360 profile, audience segmentation, RFM scoring, product '
                   'recommendations, cross-sell, upsell, omnichannel orchestration, CLTV, '
                   'predictive analytics, Looker Studio, data synchronization, presentation, deck, '
                   'slides, KFC France, Yumpingo\n'
                   'Notes & Status: Content is targeted explicitly at the Retail and E-commerce '
                   'industries. No publication date is explicitly listed. Features customer quotes '
                   'from KFC France and Yumpingo. Validated for use in Enterprise sales motions '
                   'regarding the Brevo CDP.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP (Customer Data Platform)',
                                   'Segmentation',
                                   'Data Integration',
                                   'Retail Marketing',
                                   'Marketing Automation'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'acommeassure-success-story-fr',
        'company': 'AcommeAssure',
        'title': 'AcommeAssure',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'insurance',
        'url': 'https://www.brevo.com/fr/resources/acommeassure-success-story/',
        'key_metrics': 'This French insurance brokerage (Euroassurance/Vilavi group) went from '
                       'having zero visibility into their relationship-marketing KPIs to a unified '
                       'Customer Data Platform -- enabling precise segmentation and stable '
                       'SFTP/API data flows with their internal CRM.',
        'context': '1. Master Summary\n'
                   'AcommeAssure (Euroassurance), courtier en assurance français intégré au groupe '
                   "Vilavi, a déployé la CDP et l'Automation Brevo pour résoudre trois problèmes "
                   'critiques : données fragmentées, ciblages limités et absence de visibilité sur '
                   "les KPIs marketing. Grâce à Brevo, l'entreprise centralise ses profils "
                   'clients, affine sa segmentation et stabilise ses flux techniques (SFTP/API) '
                   'pour synchroniser ses communications avec son CRM interne. Résultat : une '
                   "infrastructure data pérenne qui permet d'industrialiser le marketing "
                   'relationnel dans un secteur où confiance et réactivité sont essentielles.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Project Exploration — pour les prospects qui souffrent '
                   "de data silos ou d'un manque de visibilité sur la performance de leurs "
                   'campagnes.\n'
                   'Profil: ETI dans un secteur réglementé (finance, assurance, services) avec un '
                   'CRM interne et des flux techniques complexes (API/SFTP), cherchant à unifier '
                   "leurs données et mesurer l'impact de leurs actions marketing.\n"
                   'Pitch: "Vous me dites que vos équipes pilotent leurs campagnes un peu à '
                   "l'aveugle et que votre segmentation est limitée par des données fragmentées — "
                   "c'est exactement le problème qu'AcommeAssure a résolu avec la CDP Brevo, en "
                   'centralisant tous leurs profils pour enfin créer des segments précis et '
                   'mesurer leurs KPIs."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '• CDP comme fondation data : centralisation des profils clients pour une '
                   'segmentation précise, là où les données étaient auparavant fragmentées.\n'
                   '• Visibilité retrouvée sur les KPIs : les équipes peuvent désormais mesurer et '
                   "analyser l'impact réel de leurs actions marketing.\n"
                   '• Stabilisation des flux techniques : synchronisation fiable via SFTP/API '
                   'entre Brevo et le CRM interne.\n'
                   '• Industrialisation des parcours automatisés : déploiement de scénarios CRM '
                   'scalables et expérimentation régulière.\n'
                   '• Cas pertinent pour les secteurs réglementés : démontre la capacité de Brevo '
                   "à s'intégrer dans des écosystèmes techniques complexes.\n"
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   'Aucun KPI ou chiffre spécifique inclus dans cet asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'CDP, customer data platform, data unification, segmentation, marketing '
                   'automation, CRM integration, SFTP, API, insurance, assurance, courtage, '
                   'fintech, B2B financial services, marketing relationnel, KPIs, campaign '
                   'performance, data silos, omnichannel, email marketing, automated journeys, '
                   'parcours automatisés, mid-market, ETI, regulated industry, Brevo CDP, Brevo '
                   'Automation, Datenanreicherung, Kundensegmentierung, données clients unifiées, '
                   'ciblage précis, mesure performance, cas client CDP, success story assurance',
        'pain_points': '',
        'brevo_features_tags': [   'Customer Data Platform (CDP)',
                                   'Marketing Automation',
                                   'Advanced Segmentation',
                                   'SFTP/API Data Integration'],
        'best_for_verticals': ['insurance'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'aligro-case-study-case-study-de',
        'company': 'Aligro Case Study',
        'title': 'Aligro Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/de-use-case-aligro-wallet-2024-sls',
        'key_metrics': 'Aligro, a 1,000-employee Swiss grocery wholesaler with 14 stores, put its '
                       "loyalty card straight onto customers' phones via Brevo's Mobile Wallet — "
                       'boosting purchase frequency, offer visibility, and foot traffic both '
                       'in-store and online.',
        'context': 'Aligro, a specialist in wholesale gastronomy and a pioneer in Switzerland, has '
                   'chosen the Mobile Wallet to efficiently market all offers related to the '
                   'customer card, which is accessible to both business and private customers.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Retail & Wholesale'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'all-use-cases-of-the-wallet-ebook-de',
        'company': 'All use cases of the wallet',
        'title': 'All use cases of the wallet',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/de-anwendungsfaelle-mobile-wallet-2024-sls',
        'key_metrics': 'One Brevo Wallet client pegged its ROI on mobile wallet campaigns at '
                       '36.5x, driving a 3% lift in total revenue — this guide covers 12+ use '
                       'cases (digital loyalty cards, discount coupons, boarding passes) across '
                       'retail, travel, and events.',
        'context': 'This asset gives an overview of all use cases of the mobile wallet. With the '
                   'Mobile Wallet, you can digitally display a wide range of marketing content. '
                   'From tickets and discount coupons to loyalty cards, the Mobile Wallet offers '
                   'you a variety of options for strengthening your customer loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Cards',
                                   'Discount Coupons',
                                   'Push Notifications'],
        'best_for_verticals': [   'entertainment',
                                  'tech_saas',
                                  'public_sector',
                                  'hospitality',
                                  'retail',
                                  'ecommerce',
                                  'media_publishing'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'alltricks-case-study-case-study-fr',
        'company': 'Alltricks Case Study',
        'title': 'Alltricks Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/success-story-alltricks-fr-2024',
        'key_metrics': 'Alltricks (part of the Decathlon group) sends 250M emails a year at a >99% '
                       'deliverability rate through Brevo, and its personalized cart-triggered '
                       'promo emails alone pull a 46% open rate and 28% click rate.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Marketing Automation',
                                   'Email Deliverability',
                                   'Ecommerce'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'alltricks-case-study-case-study-en',
        'company': 'Alltricks Case Study',
        'title': 'Alltricks Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/Alltricks-case-study-EN-0125-sls',
        'key_metrics': 'Alltricks (part of the Decathlon group) sends 250M emails a year at a >99% '
                       'deliverability rate through Brevo, and its personalized cart-triggered '
                       'promo emails alone pull a 46% open rate and 28% click rate.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Marketing Automation',
                                   'Email Deliverability',
                                   'Ecommerce'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'alltricks-case-study-case-study-de',
        'company': 'Alltricks Case Study',
        'title': 'Alltricks Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/alltricks-case-study-de-sls',
        'key_metrics': 'Alltricks (part of the Decathlon group) sends 250M emails a year at a >99% '
                       'deliverability rate through Brevo, and its personalized cart-triggered '
                       'promo emails alone pull a 46% open rate and 28% click rate.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Marketing Automation',
                                   'Email Deliverability',
                                   'Ecommerce'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'alltricks-onepager-case-study-fr',
        'company': 'Alltricks Onepager',
        'title': 'Alltricks Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-alltricks-2-fr-sls',
        'key_metrics': 'Alltricks generated €11,690 from a single push notification campaign, on '
                       'top of 250M emails/year sent at up to 46% open and 28% click-through rates '
                       'via Brevo.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience in a one page.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Push Notifications', 'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'alltricks-onepager-case-study-en',
        'company': 'Alltricks Onepager',
        'title': 'Alltricks Onepager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-alltricks-2-en-sls',
        'key_metrics': 'Alltricks generated €11,690 from a single push notification campaign, on '
                       'top of 250M emails/year sent at up to 46% open and 28% click-through rates '
                       'via Brevo.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience in a one page.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Push Notifications', 'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'alltricks-onepager-case-study-es',
        'company': 'Alltricks Onepager',
        'title': 'Alltricks Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-alltricks-es-sls',
        'key_metrics': 'Alltricks generated €11,690 from a single push notification campaign, on '
                       'top of 250M emails/year sent at up to 46% open and 28% click-through rates '
                       'via Brevo.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience in a one page.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Push Notifications', 'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'alltricks-onepager-case-study-de',
        'company': 'Alltricks Onepager',
        'title': 'Alltricks Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/new-onepager-alltricks-de-sls',
        'key_metrics': 'Alltricks generated €11,690 from a single push notification campaign, on '
                       'top of 250M emails/year sent at up to 46% open and 28% click-through rates '
                       'via Brevo.',
        'context': 'Discover how Alltricks uses Brevo to boost its growth and improve customer '
                   'experience in a one page.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Push Notifications', 'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'alltricks-push-case-study-case-study-fr',
        'company': 'Alltricks Push Case Study',
        'title': 'Alltricks Push Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/usecase-alltricks-push-fr-sls',
        'key_metrics': 'See how Alltricks boosted conversion by pairing its mobile wallet loyalty '
                       'program with targeted, personalized push notifications.',
        'context': 'Find out how Alltricks, leader in e-commerce in the field of cycling and '
                   'sport, has taken advantage of Push notifications.',
        'pain_points': '',
        'brevo_features_tags': ['Push Notifications', 'Mobile Wallet', 'Ecommerce'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'aquarelle-onepager-case-study-fr',
        'company': 'Aquarelle Onepager',
        'title': 'Aquarelle Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/case-study-aquarelle-2-fr-sls',
        'key_metrics': 'Aquarelle unified 3M+ contacts and layered email, SMS, web push, WhatsApp, '
                       'and mobile wallet into one omnichannel strategy with Brevo to sharpen '
                       'engagement and conversion.',
        'context': 'Discover how Aquarelle uses Brevo to boost your multi-channel strategy, in a '
                   'one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'SMS Marketing',
                                   'Push Notifications',
                                   'WhatsApp Marketing',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'aquarelle-onepager-case-study-en',
        'company': 'Aquarelle Onepager',
        'title': 'Aquarelle Onepager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/onepager-aquarelle-en-sls',
        'key_metrics': 'Aquarelle unified 3M+ contacts and layered email, SMS, web push, WhatsApp, '
                       'and mobile wallet into one omnichannel strategy with Brevo to sharpen '
                       'engagement and conversion.',
        'context': 'Discover how Aquarelle uses Brevo to boost your multi-channel strategy, in a '
                   'one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'SMS Marketing',
                                   'Push Notifications',
                                   'WhatsApp Marketing',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'aquarelle-onepager-case-study-de',
        'company': 'Aquarelle Onepager',
        'title': 'Aquarelle Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/onepager-aquarelle-de-sls',
        'key_metrics': 'Aquarelle unified 3M+ contacts and layered email, SMS, web push, WhatsApp, '
                       'and mobile wallet into one omnichannel strategy with Brevo to sharpen '
                       'engagement and conversion.',
        'context': 'Discover how Aquarelle uses Brevo to boost your multi-channel strategy, in a '
                   'one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'SMS Marketing',
                                   'Push Notifications',
                                   'WhatsApp Marketing',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'aquarelle-onepager-case-study-es',
        'company': 'Aquarelle Onepager',
        'title': 'Aquarelle Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/onepager-aquarelle-es-sls',
        'key_metrics': 'Aquarelle unified 3M+ contacts and layered email, SMS, web push, WhatsApp, '
                       'and mobile wallet into one omnichannel strategy with Brevo to sharpen '
                       'engagement and conversion.',
        'context': 'Discover how Aquarelle uses Brevo to boost your multi-channel strategy, in a '
                   'one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Omnichannel Marketing',
                                   'SMS Marketing',
                                   'Push Notifications',
                                   'WhatsApp Marketing',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'aquarelle-s-appuie-sur-brevo-pour-dynamiser-sa-strat-gie-mul',
        'company': 'Aquarelle s’appuie sur Brevo pour dynamiser sa stratégie multicanale',
        'title': 'Aquarelle s’appuie sur Brevo pour dynamiser sa stratégie multicanale',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://www.brevo.com/fr/success-stories/aquarelle/',
        'key_metrics': 'This French online florist (3M-user database) sees SMS convert 10 points '
                       "higher than email -- using Brevo's all-in-one suite (segmentation + "
                       'email/SMS/WhatsApp/push/wallet) to reactivate dormant customers and lower '
                       'acquisition costs.',
        'context': 'This French online florist (3M-user database) sees SMS convert 10 points '
                   "higher than email -- using Brevo's all-in-one suite (segmentation + "
                   'email/SMS/WhatsApp/push/wallet) to reactivate dormant customers and lower '
                   'acquisition costs.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Campaigns',
                                   'Marketing Automation',
                                   'Omnichannel (WhatsApp, Web Push, Wallet)',
                                   'Contact Segmentation',
                                   'CRM Suite'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Consolidator', 'Feature Specialist', 'Saver']},
    {   'id': 'atlas-for-men-use-case-internal-use-case-study-fr',
        'company': 'Atlas For Men Use Case (Internal Use)',
        'title': 'Atlas For Men Use Case (Internal Use)',
        'type': 'case_study',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/usecase-afm-push-fr-sls',
        'key_metrics': 'Atlas For Men combined a mobile wallet loyalty card (with a €10 welcome '
                       "offer) and push notifications via Brevo's Captain Wallet to re-engage "
                       'customers and boost conversion.',
        'context': "How is Atlas For Men, Europe's leading outdoor e-commerce company, using a "
                   'winning combination of mobile wallet and push notifications to improve '
                   'customer engagement and boost conversions?',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Push Notifications', 'Loyalty Programs'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'au-forum-du-b-timent-wallet-b2b-case-study-case-study-fr',
        'company': 'Au Forum du Bâtiment - Wallet B2B Case study',
        'title': 'Au Forum du Bâtiment - Wallet B2B Case study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/ebook-afdb-use-case-fr-sls',
        'key_metrics': "Au Forum du Bâtiment adopted Brevo's mobile wallet as a brand-new channel "
                       'to deepen B2B customer relationships — no app download required.',
        'context': 'Au Forum du Bâtiment digitized its customer card in Apple and Google Wallet to '
                   'modernize B2B relations and streamline client identification. This mobile '
                   'channel enables instant communication, personalized offers, and improved '
                   'customer engagement across 100 stores.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'B2B Marketing', 'Customer Engagement'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'best-western-case-study-case-study-de',
        'company': 'Best Western Case Study',
        'title': 'Best Western Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/de-use-case-best-western-wallet-2024-sls',
        'key_metrics': "Best Western used Brevo's Mobile Wallet to reactivate lapsed guests and "
                       "strengthen loyalty — putting hotel perks directly on travelers' phones.",
        'context': 'Best Western France, the largest network of independent hotels in France, has '
                   'chosen Mobile Wallet to achieve its goal of developing a digital point of '
                   'contact as a solution for an economic stimulus plan to help it emerge from the '
                   'first lockdown, while strengthening and consolidating customer loyalty.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Travel & Hospitality'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'bfcm-ebook-2024-ebook-en',
        'company': 'BFCM EBOOK 2024',
        'title': 'BFCM EBOOK 2024',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ent-ebook-bfcm-2024-sls',
        'key_metrics': 'A record 200.4 million shoppers (134.2M online) shopped Black Friday/Cyber '
                       "Monday last year per the NRF — Brevo's BFCM playbook shows how to scale "
                       'and optimize campaigns to capture that surge.',
        'context': 'Brevo’s Key to Black Friday Success',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'Ecommerce Campaigns',
                                   'Seasonal Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate']},
    {   'id': 'bfcm-ebook-2024-ebook-fr',
        'company': 'BFCM EBOOK 2024',
        'title': 'BFCM EBOOK 2024',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ent-ebook-bfcm-fr-2024-sls',
        'key_metrics': 'A record 200.4 million shoppers (134.2M online) shopped Black Friday/Cyber '
                       "Monday last year per the NRF — Brevo's BFCM playbook shows how to scale "
                       'and optimize campaigns to capture that surge.',
        'context': 'Brevo’s Key to Black Friday Success',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'Ecommerce Campaigns',
                                   'Seasonal Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate']},
    {   'id': 'bfcm-ebook-2024-ebook-de',
        'company': 'BFCM EBOOK 2024',
        'title': 'BFCM EBOOK 2024',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/ent-ebook-bfcm-de-2024-sls',
        'key_metrics': 'A record 200.4 million shoppers (134.2M online) shopped Black Friday/Cyber '
                       "Monday last year per the NRF — Brevo's BFCM playbook shows how to scale "
                       'and optimize campaigns to capture that surge.',
        'context': 'Brevo’s Key to Black Friday Success',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'Ecommerce Campaigns',
                                   'Seasonal Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate']},
    {   'id': 'blueprint-for-success-in-travel-and-tourism-ebook-en',
        'company': 'Blueprint for Success in Travel and Tourism',
        'title': 'Blueprint for Success in Travel and Tourism',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/blueprint-travel-tourism-2024-sls',
        'key_metrics': "Brevo's Blueprint for Travel & Tourism tackles fragmented guest "
                       'communication by centralizing every touchpoint, unifying guest data for '
                       'precise targeting, and using mobile wallet to make loyalty programs '
                       'seamless end-to-end.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Travel '
                   'industry (and how Brevo can solve them). Case study from Suntranfers and '
                   'Wallet case study from Corsair',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Mobile Wallet',
                                   'Enterprise Marketing',
                                   'Travel & Hospitality'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'blueprint-for-success-in-travel-and-tourism-ebook-fr',
        'company': 'Blueprint for Success in Travel and Tourism',
        'title': 'Blueprint for Success in Travel and Tourism',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/fr-blueprint-travel-tourism-2025-sls',
        'key_metrics': "Brevo's Blueprint for Travel & Tourism tackles fragmented guest "
                       'communication by centralizing every touchpoint, unifying guest data for '
                       'precise targeting, and using mobile wallet to make loyalty programs '
                       'seamless end-to-end.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Travel '
                   'industry (and how Brevo can solve them). Case study from Suntranfers and '
                   'Wallet case study from Corsair',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Mobile Wallet',
                                   'Enterprise Marketing',
                                   'Travel & Hospitality'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'blueprint-for-success-in-travel-and-tourism-ebook-de',
        'company': 'Blueprint for Success in Travel and Tourism',
        'title': 'Blueprint for Success in Travel and Tourism',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/de-blueprint-travel-tourism-2025-sls',
        'key_metrics': "Brevo's Blueprint for Travel & Tourism tackles fragmented guest "
                       'communication by centralizing every touchpoint, unifying guest data for '
                       'precise targeting, and using mobile wallet to make loyalty programs '
                       'seamless end-to-end.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Travel '
                   'industry (and how Brevo can solve them). Case study from Suntranfers and '
                   'Wallet case study from Corsair',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Mobile Wallet',
                                   'Enterprise Marketing',
                                   'Travel & Hospitality'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'bora-case-study-case-study-de',
        'company': 'BORA case study',
        'title': 'BORA case study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/bora-case-study-sls',
        'key_metrics': 'BORA, a premium kitchen appliance maker operating in 40+ countries, runs '
                       'email campaigns on Brevo at a 42% average open rate and just a 0.44% '
                       'unsubscribe rate.',
        'context': 'Bora uses Brevo to centralize and automate their customer communication across '
                   'email and WhatsApp, enabling efficient client management and personalized '
                   'interactions. This has helped them save time, improve organization, and '
                   'enhance their customer relationships.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Marketing Automation'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'bora-case-study-case-study-de-2',
        'company': 'BORA case study',
        'title': 'BORA case study - Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/onepager-bora-de-sls',
        'key_metrics': "BORA's Brevo-powered welcome series hits up to 89% open rate and 59% click "
                       'rate, while its WhatsApp newsletters reach up to 85% opens.',
        'context': 'Onepager for internal use to show clients. \n'
                   'BORA uses Brevo to centralize and automate their customer communication across '
                   'email and WhatsApp, enabling efficient client management and personalized '
                   'interactions. This has helped them save time, improve organization, and '
                   'enhance their customer relationships.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'WhatsApp Marketing',
                                   'Marketing Automation',
                                   'Ecommerce Integrations'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'brevo-marketing-benchmark-2025-ebook-fr',
        'company': 'Brevo Marketing Benchmark 2025',
        'title': 'Brevo Marketing Benchmark 2025',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/benchmark-fr-2025-sls',
        'key_metrics': "Brevo's 2025 benchmark of billions of messages shows average email open "
                       'rates of 31.22% and click-to-open of 11.17%, while WhatsApp usage grew '
                       '101.8% and 30% of users return to interact after a push notification.',
        'context': 'The Brevo Marketing Benchmark 2025 offers a comprehensive overview of email '
                   'marketing KPIs and omnichannel trends, based on data from billions of messages '
                   'sent in 2024 by Brevo clients (you find the exact methodology in each report). '
                   'It highlights average email KPIs by region, industry and company size, while '
                   'exploring the performance of key channels like WhatsApp, SMS, push '
                   'notifications, chat, and mobile wallets. A must-have resource to benchmark '
                   'your results, identify areas for improvement, and refine your omnichannel '
                   'marketing strategy with actionable insights.\n'
                   '\n'
                   'The report exists in 3 editions (based on different data sets) : \n'
                   '—> French version for a report focusing only on French market\n'
                   '—> German version for a report focusing on DACH region\n'
                   '—> English version for a global report',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'WhatsApp',
                                   'Push Notifications',
                                   'Mobile Wallet',
                                   'SMS Marketing',
                                   'Omnichannel Marketing'],
        'best_for_verticals': [   'ecommerce',
                                  'retail',
                                  'media_publishing',
                                  'entertainment',
                                  'hospitality',
                                  'public_sector',
                                  'fintech',
                                  'tech_saas',
                                  'nonprofit',
                                  'b2b_services',
                                  'education',
                                  'transportation',
                                  'health'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'brevo-marketing-benchmark-2025-ebook-de',
        'company': 'Brevo Marketing Benchmark 2025',
        'title': 'Brevo Marketing Benchmark 2025',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/dach-marketing-benchmark-2025-sls',
        'key_metrics': "Brevo's 2025 benchmark of billions of messages shows average email open "
                       'rates of 31.22% and click-to-open of 11.17%, while WhatsApp usage grew '
                       '101.8% and 30% of users return to interact after a push notification.',
        'context': 'The Brevo Marketing Benchmark 2025 offers a comprehensive overview of email '
                   'marketing KPIs and omnichannel trends, based on data from billions of messages '
                   'sent in 2024 by Brevo clients (you find the exact methodology in each report). '
                   'It highlights average email KPIs by region, industry and company size, while '
                   'exploring the performance of key channels like WhatsApp, SMS, push '
                   'notifications, chat, and mobile wallets. A must-have resource to benchmark '
                   'your results, identify areas for improvement, and refine your omnichannel '
                   'marketing strategy with actionable insights.\n'
                   '\n'
                   'The report exists in 3 editions (based on different data sets) : \n'
                   '—> French version for a report focusing only on French market\n'
                   '—> German version for a report focusing on DACH region\n'
                   '—> English version for a global report',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'WhatsApp',
                                   'Push Notifications',
                                   'Mobile Wallet',
                                   'SMS Marketing',
                                   'Omnichannel Marketing'],
        'best_for_verticals': [   'ecommerce',
                                  'retail',
                                  'media_publishing',
                                  'entertainment',
                                  'hospitality',
                                  'public_sector',
                                  'fintech',
                                  'tech_saas',
                                  'nonprofit',
                                  'b2b_services',
                                  'education',
                                  'transportation',
                                  'health'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'brevo-marketing-benchmark-2025-ebook-en',
        'company': 'Brevo Marketing Benchmark 2025',
        'title': 'Brevo Marketing Benchmark 2025',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/global-marketing-benchmark-2025-sls',
        'key_metrics': "Brevo's 2025 benchmark of billions of messages shows average email open "
                       'rates of 31.22% and click-to-open of 11.17%, while WhatsApp usage grew '
                       '101.8% and 30% of users return to interact after a push notification.',
        'context': 'The Brevo Marketing Benchmark 2025 offers a comprehensive overview of email '
                   'marketing KPIs and omnichannel trends, based on data from billions of messages '
                   'sent in 2024 by Brevo clients (you find the exact methodology in each report). '
                   'It highlights average email KPIs by region, industry and company size, while '
                   'exploring the performance of key channels like WhatsApp, SMS, push '
                   'notifications, chat, and mobile wallets. A must-have resource to benchmark '
                   'your results, identify areas for improvement, and refine your omnichannel '
                   'marketing strategy with actionable insights.\n'
                   '\n'
                   'The report exists in 3 editions (based on different data sets) : \n'
                   '—> French version for a report focusing only on French market\n'
                   '—> German version for a report focusing on DACH region\n'
                   '—> English version for a global report',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'WhatsApp',
                                   'Push Notifications',
                                   'Mobile Wallet',
                                   'SMS Marketing',
                                   'Omnichannel Marketing'],
        'best_for_verticals': [   'ecommerce',
                                  'retail',
                                  'media_publishing',
                                  'entertainment',
                                  'hospitality',
                                  'public_sector',
                                  'fintech',
                                  'tech_saas',
                                  'nonprofit',
                                  'b2b_services',
                                  'education',
                                  'transportation',
                                  'health'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'brevo-s-blueprint-for-success-in-ecommerce-ebook-en',
        'company': 'Brevo’s Blueprint for Success in Ecommerce',
        'title': 'Brevo’s Blueprint for Success in Ecommerce',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Blueprint-ecommerce-sls',
        'key_metrics': '26% of Gen Z and Millennial shoppers have already switched brands over a '
                       "poor experience, and Brevo's Ecommerce Blueprint shows how the top 10% of "
                       "loyal customers can drive up to 50% of a brand's ROI through a well-built "
                       'loyalty program.',
        'context': 'Ebook exploring Brevo’s solutions for ecommerce businesses. It provides an '
                   'introduction to Brevo’s Loyalty Program, How to provide excellent customer '
                   'experiences with CDP (also in Blueprint for Retail), Introduces how Brevo '
                   'helps businesses comply with data regulations, How to accelerate growth and '
                   'not costs, and a case study from NOTSHY.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Loyalty Programs',
                                   'CRM',
                                   'Email Marketing',
                                   'SMS',
                                   'Data Compliance'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist', 'Saver']},
    {   'id': 'brevo-s-blueprint-for-success-in-media-and-publishing-ebook-',
        'company': 'Brevo’s Blueprint for Success in Media and Publishing',
        'title': 'Brevo’s Blueprint for Success in Media and Publishing',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/blueprint-media-publishing-2024-sls',
        'key_metrics': 'Media and publishing brands lose engagement to fragmented, disconnected '
                       "channels — Brevo's Media & Publishing Blueprint shows how unifying email, "
                       'SMS, and social under one platform (plus a CDP) turns scattered campaigns '
                       'into measurable, cross-platform performance.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Media '
                   'industry (and how Brevo can solve them)',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'SMS',
                                   'CDP',
                                   'Personalization',
                                   'Omnichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'brevo-s-blueprint-for-success-in-media-and-publishing-ebook--2',
        'company': 'Brevo’s Blueprint for Success in Media and Publishing',
        'title': 'Brevo’s Blueprint for Success in Media and Publishing',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/fr-blueprint-media-publishing-2024-sls',
        'key_metrics': 'Media and publishing brands lose engagement to fragmented, disconnected '
                       "channels — Brevo's Media & Publishing Blueprint shows how unifying email, "
                       'SMS, and social under one platform (plus a CDP) turns scattered campaigns '
                       'into measurable, cross-platform performance.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Media '
                   'industry (and how Brevo can solve them)',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'SMS',
                                   'CDP',
                                   'Personalization',
                                   'Omnichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'brevo-s-blueprint-for-success-in-media-and-publishing-ebook--3',
        'company': 'Brevo’s Blueprint for Success in Media and Publishing',
        'title': 'Brevo’s Blueprint for Success in Media and Publishing',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/de-blueprint-media-publishing-2024-sls',
        'key_metrics': 'Media and publishing brands lose engagement to fragmented, disconnected '
                       "channels — Brevo's Media & Publishing Blueprint shows how unifying email, "
                       'SMS, and social under one platform (plus a CDP) turns scattered campaigns '
                       'into measurable, cross-platform performance.',
        'context': 'Industry-specifc ebook covering the the 3 main problems facing the Media '
                   'industry (and how Brevo can solve them)',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email Marketing',
                                   'SMS',
                                   'CDP',
                                   'Personalization',
                                   'Omnichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'brevo-s-blueprint-for-success-in-retail-ebook-en',
        'company': 'Brevo’s Blueprint for Success in Retail',
        'title': 'Brevo’s Blueprint for Success in Retail',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/Blueprint-retail-sls',
        'key_metrics': "Brevo's Retail Blueprint shows how top retailers combine in-store Mobile "
                       'Wallet marketing with a unified Customer Data Platform (CDP) to turn '
                       'one-time shoppers into repeat buyers across digital and physical '
                       'touchpoints.',
        'context': '1. Master Summary\n'
                   'This blueprint is a strategic guide for mid-market and enterprise retail '
                   'brands struggling with fragmented data, disconnected shopping experiences, and '
                   "costly tech stacks. It outlines how to use Brevo's omnichannel "
                   'capabilities—specifically Wallet, the data platform, and advanced marketing '
                   'automation—to drive in-store traffic, unify customer profiles, and scale '
                   'efficiently without budget bloat.\n'
                   '2. Search Keywords & AI Tags\n'
                   'Retail, Enterprise, BDP, CDP, Wallet, Geo-fencing, Omnichannel, Data Silos, '
                   'RFM scoring, Predictive Sending, Marketing Automation, Nestor case study, Foot '
                   'traffic, Tech stack consolidation\n'
                   '3. Sales Context: When to share this\n'
                   'Use this during the discovery or solution alignment phase when speaking to Pro '
                   'or Enterprise retail prospects (e-commerce, brick-and-mortar, or hybrid). It '
                   'is highly effective for prospects complaining about the rigid/high costs of '
                   'their current CRM stack, struggling to connect their POS data with their '
                   'online data, or looking for innovative ways to drive foot traffic using mobile '
                   'wallets.\n'
                   '4. Key Takeaways\n'
                   "• Bridge the Online-to-Offline Gap:\xa0Brevo Wallet's geo-fencing capabilities "
                   'allow retailers to send targeted push notifications (offers, back-in-stock, '
                   'click-and-collect) the moment a customer enters a specific radius near a '
                   'physical store.\n'
                   '• Unify the Customer View:\xa0Brands can overcome data silos by centralizing '
                   'POS, e-commerce, and offline data into a single identity, cleaning up '
                   'duplicates along the way.\n'
                   '• Smarter Segmentation & Timing:\xa0Leverage built-in RFM and LTV scoring '
                   'alongside Predictive Sending AI to ensure customers receive the right message '
                   'at the exact right time, preventing communication fatigue.\n'
                   '• Scale Without Cost Penalties:\xa0Brevo’s Enterprise plan offers unlimited '
                   'contact storage and modular feature adoption so retail brands only pay for the '
                   'value they generate as they grow.\n'
                   '5. Key KPIs, Figures & Insights\n'
                   '• Wallet ROI:\xa0Boosts revenue per user by up to 45%.\n'
                   '• Wallet Cost-Efficiency:\xa040% less expensive than SMS, with a reach 3x that '
                   'of a native mobile app.\n'
                   '• Retail Context:\xa070% of retail sales still happen in-store, making '
                   'localized omnichannel touchpoints crucial.\n'
                   '• Brevo Performance:\xa097% deliverability rate across 180 countries.\n'
                   '6. Product Accuracy Check\n'
                   'The features and value propositions are highly relevant, and there is no '
                   'outdated "Sendinblue" branding. However, please note one important positioning '
                   'nuance: The asset heavily references "Brevo CDP" as the solution to data '
                   'silos. According to our current internal positioning, remember that we refer '
                   'to this as the Brevo Data Platform (BDP), which is our native data foundation '
                   'embedded across plans. When speaking to prospects, avoid framing it as a '
                   'separate add-on "CDP" product. Otherwise, the references to Wallet, unlimited '
                   'contacts, predictive sending, and Enterprise capabilities are accurate and up '
                   'to date.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'CDP',
                                   'Email Marketing',
                                   'SMS',
                                   'Marketing Automation',
                                   'Omnichannel Retail'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'brevo-s-blueprint-for-success-in-retail-ebook-fr',
        'company': 'Brevo’s Blueprint for Success in Retail',
        'title': 'Brevo’s Blueprint for Success in Retail',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/FR-Blueprint-Retail-sls',
        'key_metrics': "Brevo's Retail Blueprint shows how top retailers combine in-store Mobile "
                       'Wallet marketing with a unified Customer Data Platform (CDP) to turn '
                       'one-time shoppers into repeat buyers across digital and physical '
                       'touchpoints.',
        'context': '1. Master Summary\n'
                   'This blueprint is a strategic guide for mid-market and enterprise retail '
                   'brands struggling with fragmented data, disconnected shopping experiences, and '
                   "costly tech stacks. It outlines how to use Brevo's omnichannel "
                   'capabilities—specifically Wallet, the data platform, and advanced marketing '
                   'automation—to drive in-store traffic, unify customer profiles, and scale '
                   'efficiently without budget bloat.\n'
                   '2. Search Keywords & AI Tags\n'
                   'Retail, Enterprise, BDP, CDP, Wallet, Geo-fencing, Omnichannel, Data Silos, '
                   'RFM scoring, Predictive Sending, Marketing Automation, Nestor case study, Foot '
                   'traffic, Tech stack consolidation\n'
                   '3. Sales Context: When to share this\n'
                   'Use this during the discovery or solution alignment phase when speaking to Pro '
                   'or Enterprise retail prospects (e-commerce, brick-and-mortar, or hybrid). It '
                   'is highly effective for prospects complaining about the rigid/high costs of '
                   'their current CRM stack, struggling to connect their POS data with their '
                   'online data, or looking for innovative ways to drive foot traffic using mobile '
                   'wallets.\n'
                   '4. Key Takeaways\n'
                   "• Bridge the Online-to-Offline Gap:\xa0Brevo Wallet's geo-fencing capabilities "
                   'allow retailers to send targeted push notifications (offers, back-in-stock, '
                   'click-and-collect) the moment a customer enters a specific radius near a '
                   'physical store.\n'
                   '• Unify the Customer View:\xa0Brands can overcome data silos by centralizing '
                   'POS, e-commerce, and offline data into a single identity, cleaning up '
                   'duplicates along the way.\n'
                   '• Smarter Segmentation & Timing:\xa0Leverage built-in RFM and LTV scoring '
                   'alongside Predictive Sending AI to ensure customers receive the right message '
                   'at the exact right time, preventing communication fatigue.\n'
                   '• Scale Without Cost Penalties:\xa0Brevo’s Enterprise plan offers unlimited '
                   'contact storage and modular feature adoption so retail brands only pay for the '
                   'value they generate as they grow.\n'
                   '5. Key KPIs, Figures & Insights\n'
                   '• Wallet ROI:\xa0Boosts revenue per user by up to 45%.\n'
                   '• Wallet Cost-Efficiency:\xa040% less expensive than SMS, with a reach 3x that '
                   'of a native mobile app.\n'
                   '• Retail Context:\xa070% of retail sales still happen in-store, making '
                   'localized omnichannel touchpoints crucial.\n'
                   '• Brevo Performance:\xa097% deliverability rate across 180 countries.\n'
                   '6. Product Accuracy Check\n'
                   'The features and value propositions are highly relevant, and there is no '
                   'outdated "Sendinblue" branding. However, please note one important positioning '
                   'nuance: The asset heavily references "Brevo CDP" as the solution to data '
                   'silos. According to our current internal positioning, remember that we refer '
                   'to this as the Brevo Data Platform (BDP), which is our native data foundation '
                   'embedded across plans. When speaking to prospects, avoid framing it as a '
                   'separate add-on "CDP" product. Otherwise, the references to Wallet, unlimited '
                   'contacts, predictive sending, and Enterprise capabilities are accurate and up '
                   'to date.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'CDP',
                                   'Email Marketing',
                                   'SMS',
                                   'Marketing Automation',
                                   'Omnichannel Retail'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'brevo-s-guide-to-marketing-automation-for-b2c-ebook-en',
        'company': 'Brevo’s Guide to Marketing Automation for B2C',
        'title': 'Brevo’s Guide to Marketing Automation for B2C',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/marketing-automation-b2c-2024-sls',
        'key_metrics': "Brevo's B2C automation guide shows how brands stuck with manual, "
                       'non-scaling campaigns can consolidate fragmented consumer data and '
                       'automate demand generation to directly boost marketing ROI.',
        'context': 'This ebook explains how marketers can automate their efforts to drive sales '
                   'and strengthen customer relationships.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Lead Scoring',
                                   'Email Marketing',
                                   'Consumer Data Management'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': 'brevo-s-guide-to-marketing-automation-for-b2c-ebook-de',
        'company': 'Brevo’s Guide to Marketing Automation for B2C',
        'title': 'Brevo’s Guide to Marketing Automation for B2C',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-marketing-automation-b2c-2024-sls',
        'key_metrics': "Brevo's B2C automation guide shows how brands stuck with manual, "
                       'non-scaling campaigns can consolidate fragmented consumer data and '
                       'automate demand generation to directly boost marketing ROI.',
        'context': 'This ebook explains how marketers can automate their efforts to drive sales '
                   'and strengthen customer relationships.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Lead Scoring',
                                   'Email Marketing',
                                   'Consumer Data Management'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': 'brevo-s-guide-to-marketing-automation-for-b2c-ebook-fr',
        'company': 'Brevo’s Guide to Marketing Automation for B2C',
        'title': 'Brevo’s Guide to Marketing Automation for B2C',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/fr-marketing-automation-b2c-2024-sls',
        'key_metrics': "Brevo's B2C automation guide shows how brands stuck with manual, "
                       'non-scaling campaigns can consolidate fragmented consumer data and '
                       'automate demand generation to directly boost marketing ROI.',
        'context': 'This ebook explains how marketers can automate their efforts to drive sales '
                   'and strengthen customer relationships.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'CDP',
                                   'Lead Scoring',
                                   'Email Marketing',
                                   'Consumer Data Management'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': 'brevo-s-guide-to-sustainable-email-marketing-ebook-en',
        'company': 'Brevo’s Guide to Sustainable Email Marketing',
        'title': 'Brevo’s Guide to Sustainable Email Marketing',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-sustainable-email-marketing-2024-sls',
        'key_metrics': '78% of US consumers say a sustainable lifestyle matters to them '
                       "(NielsenIQ) — Brevo's Sustainability Guide shows marketers how to cut the "
                       'carbon footprint of their email campaigns (scope 1-3 emissions) while '
                       'cutting costs and boosting brand image.',
        'context': 'In response to the growing importance of ESG factors,\xa0organizations are now '
                   'required to evaluate and mitigate their emissions. Consequently, our users, '
                   'particularly ENT clients, are increasingly interested in understanding the '
                   'carbon footprint of their email activities. In line with Brevo’s commitment to '
                   'sustainability initiatives, we have introduced a carbon footprint report that '
                   'measures the emissions generated by email campaigns and transactional emails. '
                   'This report enables our users to accurately assess (and later, following '
                   'future initiatives, reduce) their emissions resulting from sending emails.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Sustainability/ESG',
                                   'Deliverability',
                                   'Brand Reputation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Saver']},
    {   'id': 'brevo-s-guide-to-sustainable-email-marketing-ebook-fr',
        'company': 'Brevo’s Guide to Sustainable Email Marketing',
        'title': 'Brevo’s Guide to Sustainable Email Marketing',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/fr-ebook-sustainable-email-marketing-2024-sls',
        'key_metrics': '78% of US consumers say a sustainable lifestyle matters to them '
                       "(NielsenIQ) — Brevo's Sustainability Guide shows marketers how to cut the "
                       'carbon footprint of their email campaigns (scope 1-3 emissions) while '
                       'cutting costs and boosting brand image.',
        'context': 'In response to the growing importance of ESG factors,\xa0organizations are now '
                   'required to evaluate and mitigate their emissions. Consequently, our users, '
                   'particularly ENT clients, are increasingly interested in understanding the '
                   'carbon footprint of their email activities. In line with Brevo’s commitment to '
                   'sustainability initiatives, we have introduced a carbon footprint report that '
                   'measures the emissions generated by email campaigns and transactional emails. '
                   'This report enables our users to accurately assess (and later, following '
                   'future initiatives, reduce) their emissions resulting from sending emails.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Sustainability/ESG',
                                   'Deliverability',
                                   'Brand Reputation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Saver']},
    {   'id': 'brevo-s-guide-to-sustainable-email-marketing-ebook-de',
        'company': 'Brevo’s Guide to Sustainable Email Marketing',
        'title': 'Brevo’s Guide to Sustainable Email Marketing',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-ebook-sustainable-email-marketing-2024-sls',
        'key_metrics': '78% of US consumers say a sustainable lifestyle matters to them '
                       "(NielsenIQ) — Brevo's Sustainability Guide shows marketers how to cut the "
                       'carbon footprint of their email campaigns (scope 1-3 emissions) while '
                       'cutting costs and boosting brand image.',
        'context': 'In response to the growing importance of ESG factors,\xa0organizations are now '
                   'required to evaluate and mitigate their emissions. Consequently, our users, '
                   'particularly ENT clients, are increasingly interested in understanding the '
                   'carbon footprint of their email activities. In line with Brevo’s commitment to '
                   'sustainability initiatives, we have introduced a carbon footprint report that '
                   'measures the emissions generated by email campaigns and transactional emails. '
                   'This report enables our users to accurately assess (and later, following '
                   'future initiatives, reduce) their emissions resulting from sending emails.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Sustainability/ESG',
                                   'Deliverability',
                                   'Brand Reputation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Saver']},
    {   'id': 'brevo-s-handbook-for-deliverability-ebook-en',
        'company': 'Brevo’s Handbook for Deliverability',
        'title': 'Brevo’s Handbook for Deliverability',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/deliverability-handbook-2025-sls',
        'key_metrics': 'Poor inbox placement can quietly kill customer retention and revenue — '
                       "Brevo's 2025 Deliverability Handbook lays out the exact infrastructure, "
                       'authentication, list hygiene, and metrics enterprises need to protect '
                       'sender reputation while scaling email volume.',
        'context': 'Revamp of the old Deliverability ebook - a guide for deliverability success '
                   'with the Deliverability Checklist attached at the end.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Deliverability',
                                   'Email Authentication (SPF/DKIM/DMARC)',
                                   'List Management',
                                   'Segmentation',
                                   'Transactional Email',
                                   'API'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator', 'Email Specialist']},
    {   'id': 'brevo-s-handbook-for-deliverability-ebook-fr',
        'company': 'Brevo’s Handbook for Deliverability',
        'title': 'Brevo’s Handbook for Deliverability',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/fr-deliverability-handbook-2025-sls',
        'key_metrics': 'Poor inbox placement can quietly kill customer retention and revenue — '
                       "Brevo's 2025 Deliverability Handbook lays out the exact infrastructure, "
                       'authentication, list hygiene, and metrics enterprises need to protect '
                       'sender reputation while scaling email volume.',
        'context': 'Revamp of the old Deliverability ebook - a guide for deliverability success '
                   'with the Deliverability Checklist attached at the end.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Deliverability',
                                   'Email Authentication (SPF/DKIM/DMARC)',
                                   'List Management',
                                   'Segmentation',
                                   'Transactional Email',
                                   'API'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator', 'Email Specialist']},
    {   'id': 'brevo-s-handbook-for-deliverability-ebook-de',
        'company': 'Brevo’s Handbook for Deliverability',
        'title': 'Brevo’s Handbook for Deliverability',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-deliverability-ebook-2025-sls',
        'key_metrics': 'Poor inbox placement can quietly kill customer retention and revenue — '
                       "Brevo's 2025 Deliverability Handbook lays out the exact infrastructure, "
                       'authentication, list hygiene, and metrics enterprises need to protect '
                       'sender reputation while scaling email volume.',
        'context': 'Revamp of the old Deliverability ebook - a guide for deliverability success '
                   'with the Deliverability Checklist attached at the end.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Deliverability',
                                   'Email Authentication (SPF/DKIM/DMARC)',
                                   'List Management',
                                   'Segmentation',
                                   'Transactional Email',
                                   'API'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator', 'Email Specialist']},
    {   'id': 'buffalo-grill-case-study-x-wallet-case-study-fr',
        'company': 'Buffalo Grill Case Study x Wallet',
        'title': 'Buffalo Grill Case Study x Wallet',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/use-case-buffalo-grill-wallet-fr-sls',
        'key_metrics': 'Buffalo Grill activated 500K mobile wallet cards in just 6 months using '
                       'Brevo, with 47% of walletized customers returning a second time and a 92% '
                       'retention rate for their loyalty pass.',
        'context': 'How Buffalo Grill shattered the record for the most wallet cards activated in '
                   '6 months ?\n'
                   '\n'
                   "Buffalo Grill, one of France's leading restaurant chains, has chosen Wallet "
                   'Mobile to digitalise its loyalty programme and maximise customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Push Notifications',
                                   'Restaurant/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'buffalo-grill-case-study-x-wallet-case-study-en',
        'company': 'Buffalo Grill Case Study x Wallet',
        'title': 'Buffalo Grill Case Study x Wallet',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/use-case-buffalo-grill-wallet-en-sls',
        'key_metrics': 'Buffalo Grill activated 500K mobile wallet cards in just 6 months using '
                       'Brevo, with 47% of walletized customers returning a second time and a 92% '
                       'retention rate for their loyalty pass.',
        'context': 'How Buffalo Grill shattered the record for the most wallet cards activated in '
                   '6 months ?\n'
                   '\n'
                   "Buffalo Grill, one of France's leading restaurant chains, has chosen Wallet "
                   'Mobile to digitalise its loyalty programme and maximise customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Push Notifications',
                                   'Restaurant/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'buffalo-grill-case-study-x-wallet-case-study-de',
        'company': 'Buffalo Grill Case Study x Wallet',
        'title': 'Buffalo Grill Case Study x Wallet',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/use-case-buffalo-grill-wallet-de-sls',
        'key_metrics': 'Buffalo Grill activated 500K mobile wallet cards in just 6 months using '
                       'Brevo, with 47% of walletized customers returning a second time and a 92% '
                       'retention rate for their loyalty pass.',
        'context': 'How Buffalo Grill shattered the record for the most wallet cards activated in '
                   '6 months ?\n'
                   '\n'
                   "Buffalo Grill, one of France's leading restaurant chains, has chosen Wallet "
                   'Mobile to digitalise its loyalty programme and maximise customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Push Notifications',
                                   'Restaurant/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'buffalo-grill-one-pager-case-study-fr',
        'company': 'Buffalo Grill One Pager',
        'title': 'Buffalo Grill One Pager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Onepager-BuffaloGrillFR-sls',
        'key_metrics': "Buffalo Grill's 100% paperless loyalty program hit 500K wallet card "
                       'activations in 6 months, a 92% retention rate, and 75% of downloads '
                       'happening right inside the restaurant.',
        'context': 'Discover how Buffalo Grill smashed the record for the number of cards '
                   'activated on the wallet in 6 months.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Push Notifications', 'CRM'],
        'best_for_verticals': ['ecommerce', 'hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'buffalo-grill-one-pager-case-study-en',
        'company': 'Buffalo Grill One Pager',
        'title': 'Buffalo Grill One Pager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Onepager-BuffaloGrill-EN-sls',
        'key_metrics': "Buffalo Grill's 100% paperless loyalty program hit 500K wallet card "
                       'activations in 6 months, a 92% retention rate, and 75% of downloads '
                       'happening right inside the restaurant.',
        'context': 'Discover how Buffalo Grill smashed the record for the number of cards '
                   'activated on the wallet in 6 months.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Push Notifications', 'CRM'],
        'best_for_verticals': ['ecommerce', 'hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'buffalo-grill-one-pager-case-study-de',
        'company': 'Buffalo Grill One Pager',
        'title': 'Buffalo Grill One Pager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Onepager-BuffaloGrill-DE-sls',
        'key_metrics': "Buffalo Grill's 100% paperless loyalty program hit 500K wallet card "
                       'activations in 6 months, a 92% retention rate, and 75% of downloads '
                       'happening right inside the restaurant.',
        'context': 'Discover how Buffalo Grill smashed the record for the number of cards '
                   'activated on the wallet in 6 months.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Push Notifications', 'CRM'],
        'best_for_verticals': ['ecommerce', 'hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'burda-case-study-in-de-translation-from-fr-original-case-stu',
        'company': 'Burda case study in DE (translation from FR original)',
        'title': 'Burda case study in DE (translation from FR original)',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'https://www.brevo.com/fr/success-stories/burda/',
        'key_metrics': 'This German media brand (Burda Style, published in 17 languages across '
                       "100+ countries) runs its global sewing-pattern community on Brevo's "
                       'Enterprise Multi-Account solution -- with dedicated IP warmup, a '
                       'drag-and-drop builder, and automated abandoned-cart, wishlist, and '
                       'engagement-scoring scenarios across hundreds of thousands of subscribers.',
        'context': 'This German media brand (Burda Style, published in 17 languages across 100+ '
                   "countries) runs its global sewing-pattern community on Brevo's Enterprise "
                   'Multi-Account solution -- with dedicated IP warmup, a drag-and-drop builder, '
                   'and automated abandoned-cart, wishlist, and engagement-scoring scenarios '
                   'across hundreds of thousands of subscribers.',
        'pain_points': '',
        'brevo_features_tags': [   'Enterprise Multi-Account Solution',
                                   'Marketing Automation',
                                   'Advanced Segmentation',
                                   'Deliverability/IP Warmup',
                                   'Lead Scoring'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Network', 'Consolidator', 'Email Specialist']},
    {   'id': 'burda-case-study-in-de-translation-from-fr-original-case-stu-2',
        'company': 'Burda case study in DE (translation from FR original)',
        'title': 'Burda case study in DE (translation from FR original)',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://www.brevo.com/de/success-stories/burda/',
        'key_metrics': 'This German media brand (Burda Style, published in 17 languages across '
                       "100+ countries) runs its global sewing-pattern community on Brevo's "
                       'Enterprise Multi-Account solution -- with dedicated IP warmup, a '
                       'drag-and-drop builder, and automated abandoned-cart, wishlist, and '
                       'engagement-scoring scenarios across hundreds of thousands of subscribers.',
        'context': 'This German media brand (Burda Style, published in 17 languages across 100+ '
                   "countries) runs its global sewing-pattern community on Brevo's Enterprise "
                   'Multi-Account solution -- with dedicated IP warmup, a drag-and-drop builder, '
                   'and automated abandoned-cart, wishlist, and engagement-scoring scenarios '
                   'across hundreds of thousands of subscribers.',
        'pain_points': '',
        'brevo_features_tags': [   'Enterprise Multi-Account Solution',
                                   'Marketing Automation',
                                   'Advanced Segmentation',
                                   'Deliverability/IP Warmup',
                                   'Lead Scoring'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Network', 'Consolidator', 'Email Specialist']},
    {   'id': 'capturing-the-ecommerce-boom-with-multichannel-marketing-ebo',
        'company': 'Capturing the ecommerce boom with multichannel marketing',
        'title': 'Capturing the ecommerce boom with multichannel marketing',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://corp-backend.brevo.com/wp-content/uploads/2023/06/multichannel-marketing-for-ecommerce.pdf',
        'key_metrics': 'A tactical guide for meeting sky-high ecommerce customer expectations '
                       'across email, SMS, chat, and WhatsApp -- built for teams navigating an '
                       'increasingly competitive online retail space.',
        'context': 'A tactical guide for meeting sky-high ecommerce customer expectations across '
                   'email, SMS, chat, and WhatsApp -- built for teams navigating an increasingly '
                   'competitive online retail space.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Marketing',
                                   'WhatsApp Marketing',
                                   'Live Chat/Chatbot',
                                   'Ecommerce'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'ticketing-wallet-case-study-fr',
        'company': 'Ticketing Wallet',
        'title': 'Case Study - Ticketing Wallet',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'content.brevo.com/use-case-ticketing-wallet-fr-sls',
        'key_metrics': "Brevo's ticketing case study shows how e-tickets delivered straight to a "
                       "customer's mobile wallet turn event attendees into engaged, repeat "
                       'customers — no app download required.',
        'context': 'This case study shows how several companies have dematerialized access to '
                   "their events using a mobile wallet. You'll discover how having an e-ticket in "
                   'your wallet can be used to follow-up and engage customers.\n'
                   "3 French Companies : France Galop / Ruinart / Jardin d'acclimatation",
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Event Ticketing',
                                   'Push Notifications',
                                   'Media & Entertainment'],
        'best_for_verticals': ['media_publishing', 'entertainment'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'caf-kitsun-case-study-fr',
        'company': 'Café Kitsuné',
        'title': 'Case study Café Kitsuné',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/usecase-cafe-kitsune-fr-sls',
        'key_metrics': 'Cafe Kitsune turned casual coffee-shop visitors into loyal customers by '
                       "pairing Brevo's Mobile Wallet with its loyalty platform — the winning "
                       'formula behind its case study.',
        'context': 'Master summary: This case study presentation details how Café Kitsuné (Maison '
                   'Kitsuné’s coffee brand) combined Brevo’s Mobile Wallet and Loyalty Platform to '
                   'build a modern, high-engagement loyalty program. It demonstrates how they '
                   'moved away from POS-dependent loyalty systems to collect zero-party data '
                   'natively, resulting in a 98% form completion rate and a 96% wallet retention '
                   'rate.Best use / When to share: Share during the Consideration or Decision '
                   'stages with marketing and CRM leaders in Retail, Food & Beverage, or '
                   'Hospitality. It specifically resolves objections related to slow checkout '
                   'experiences, friction in loyalty enrollment, and heavy reliance on IT/POS '
                   'integrations. The deck highlights how baristas can use simple standalone '
                   'tablets/codes to trigger loyalty events without complex till integrations.Key '
                   'takeaways:\n'
                   '• Frictionless Enrollment: Achieved a 98% form completion rate via in-store QR '
                   'codes that allow customers to register directly on their phones, avoiding '
                   'checkout delays.\n'
                   '• POS Independence: Baristas use a simple code to validate visits, eliminating '
                   'the need for complex, costly integrations with the cash register system.\n'
                   '• Dynamic Tiering: Customers automatically progress through visual tiers '
                   '(Latte, Matcha, Dark Coffee) on their Wallet card, with real-time updates '
                   'driven by Brevo’s Loyalty Platform.\n'
                   '• Omnichannel Engagement: Used geolocated and targeted push notifications to '
                   'announce new menus and 24-hour flash sales, significantly driving in-store '
                   'foot traffic.\n'
                   '• Proven Retention: Delivered a 96% retention rate for the Wallet card, '
                   'proving that customers prefer native, app-free digital loyalty '
                   'solutions.Search keywords: Café Kitsuné, Maison Kitsuné, case study, customer '
                   'story, Mobile Wallet, Captain Wallet, Loyalty Platform, POS independence, '
                   'retail, food and beverage, F&B, hospitality, QR code enrollment, dynamic '
                   'tiers, geofencing, push notifications, customer engagement, zero-party data, '
                   'presentation, deck, slidesNotes & Status: Content focuses heavily on the joint '
                   'value proposition of Captain Wallet + Brevo Loyalty. No specific publication '
                   'date is included, but references to upcoming projects in Japan suggest it is a '
                   'current asset. Validated for use in Enterprise sales motions regarding Wallet '
                   'and Loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Retail/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'caf-kitsun-case-study-de',
        'company': 'Café Kitsuné',
        'title': 'Case study Café Kitsuné',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/usecase-cafe-kitsune-de-sls',
        'key_metrics': 'Cafe Kitsune turned casual coffee-shop visitors into loyal customers by '
                       "pairing Brevo's Mobile Wallet with its loyalty platform — the winning "
                       'formula behind its case study.',
        'context': 'Master summary: This case study presentation details how Café Kitsuné (Maison '
                   'Kitsuné’s coffee brand) combined Brevo’s Mobile Wallet and Loyalty Platform to '
                   'build a modern, high-engagement loyalty program. It demonstrates how they '
                   'moved away from POS-dependent loyalty systems to collect zero-party data '
                   'natively, resulting in a 98% form completion rate and a 96% wallet retention '
                   'rate.Best use / When to share: Share during the Consideration or Decision '
                   'stages with marketing and CRM leaders in Retail, Food & Beverage, or '
                   'Hospitality. It specifically resolves objections related to slow checkout '
                   'experiences, friction in loyalty enrollment, and heavy reliance on IT/POS '
                   'integrations. The deck highlights how baristas can use simple standalone '
                   'tablets/codes to trigger loyalty events without complex till integrations.Key '
                   'takeaways:\n'
                   '• Frictionless Enrollment: Achieved a 98% form completion rate via in-store QR '
                   'codes that allow customers to register directly on their phones, avoiding '
                   'checkout delays.\n'
                   '• POS Independence: Baristas use a simple code to validate visits, eliminating '
                   'the need for complex, costly integrations with the cash register system.\n'
                   '• Dynamic Tiering: Customers automatically progress through visual tiers '
                   '(Latte, Matcha, Dark Coffee) on their Wallet card, with real-time updates '
                   'driven by Brevo’s Loyalty Platform.\n'
                   '• Omnichannel Engagement: Used geolocated and targeted push notifications to '
                   'announce new menus and 24-hour flash sales, significantly driving in-store '
                   'foot traffic.\n'
                   '• Proven Retention: Delivered a 96% retention rate for the Wallet card, '
                   'proving that customers prefer native, app-free digital loyalty '
                   'solutions.Search keywords: Café Kitsuné, Maison Kitsuné, case study, customer '
                   'story, Mobile Wallet, Captain Wallet, Loyalty Platform, POS independence, '
                   'retail, food and beverage, F&B, hospitality, QR code enrollment, dynamic '
                   'tiers, geofencing, push notifications, customer engagement, zero-party data, '
                   'presentation, deck, slidesNotes & Status: Content focuses heavily on the joint '
                   'value proposition of Captain Wallet + Brevo Loyalty. No specific publication '
                   'date is included, but references to upcoming projects in Japan suggest it is a '
                   'current asset. Validated for use in Enterprise sales motions regarding Wallet '
                   'and Loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Retail/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'caf-kitsun-case-study-en',
        'company': 'Café Kitsuné',
        'title': 'Case study Café Kitsuné',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/usecase-cafe-kitsune-en-sls',
        'key_metrics': 'Cafe Kitsune turned casual coffee-shop visitors into loyal customers by '
                       "pairing Brevo's Mobile Wallet with its loyalty platform — the winning "
                       'formula behind its case study.',
        'context': 'Master summary: This case study presentation details how Café Kitsuné (Maison '
                   'Kitsuné’s coffee brand) combined Brevo’s Mobile Wallet and Loyalty Platform to '
                   'build a modern, high-engagement loyalty program. It demonstrates how they '
                   'moved away from POS-dependent loyalty systems to collect zero-party data '
                   'natively, resulting in a 98% form completion rate and a 96% wallet retention '
                   'rate.Best use / When to share: Share during the Consideration or Decision '
                   'stages with marketing and CRM leaders in Retail, Food & Beverage, or '
                   'Hospitality. It specifically resolves objections related to slow checkout '
                   'experiences, friction in loyalty enrollment, and heavy reliance on IT/POS '
                   'integrations. The deck highlights how baristas can use simple standalone '
                   'tablets/codes to trigger loyalty events without complex till integrations.Key '
                   'takeaways:\n'
                   '• Frictionless Enrollment: Achieved a 98% form completion rate via in-store QR '
                   'codes that allow customers to register directly on their phones, avoiding '
                   'checkout delays.\n'
                   '• POS Independence: Baristas use a simple code to validate visits, eliminating '
                   'the need for complex, costly integrations with the cash register system.\n'
                   '• Dynamic Tiering: Customers automatically progress through visual tiers '
                   '(Latte, Matcha, Dark Coffee) on their Wallet card, with real-time updates '
                   'driven by Brevo’s Loyalty Platform.\n'
                   '• Omnichannel Engagement: Used geolocated and targeted push notifications to '
                   'announce new menus and 24-hour flash sales, significantly driving in-store '
                   'foot traffic.\n'
                   '• Proven Retention: Delivered a 96% retention rate for the Wallet card, '
                   'proving that customers prefer native, app-free digital loyalty '
                   'solutions.Search keywords: Café Kitsuné, Maison Kitsuné, case study, customer '
                   'story, Mobile Wallet, Captain Wallet, Loyalty Platform, POS independence, '
                   'retail, food and beverage, F&B, hospitality, QR code enrollment, dynamic '
                   'tiers, geofencing, push notifications, customer engagement, zero-party data, '
                   'presentation, deck, slidesNotes & Status: Content focuses heavily on the joint '
                   'value proposition of Captain Wallet + Brevo Loyalty. No specific publication '
                   'date is included, but references to upcoming projects in Japan suggest it is a '
                   'current asset. Validated for use in Enterprise sales motions regarding Wallet '
                   'and Loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Retail/Hospitality Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'partouche-cw-brand-case-study-fr',
        'company': 'Partouche (CW brand)',
        'title': 'Case study Partouche (CW brand)',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'entertainment',
        'url': 'https://content.captainwallet.com/usecase-partouche-fr-internal',
        'key_metrics': 'French casino group Partouche turned its physical loyalty card into a '
                       'Captain Wallet mobile pass, powering personalized, real-time '
                       'communications with players directly on their phones.',
        'context': "Partouche Group transforms its players' experience thanks to the mobile "
                   "wallet! France's historic casino leader has reinvented its Players Plus "
                   "loyalty program by integrating it directly into customers' smartphones for a "
                   'fluid and engaging journey! \n'
                   '\n'
                   'Partouche has achieved a record retention rate of 95%!\n'
                   '\n'
                   '- How the Partouche loyalty card integrates into the wallet (iOS & Android)\n'
                   '- Advanced personalisation \n'
                   "- Concrete use cases & the group's expansion plans\n"
                   '- How the wallet boosts its phygital strategy',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Personalization',
                                   'Gaming/Casino'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'consumer-study-2024-de-ebook-de',
        'company': 'Consumer Study 2024 (DE)',
        'title': 'Consumer Study 2024 (DE)',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/consumer-study-de-sls',
        'key_metrics': "In Brevo's 2024 survey of 2,057 German online shoppers, email ranked as "
                       'the top communication channel and digital loyalty cards emerged as a key '
                       'driver of brand loyalty — essential benchmarks for any brand selling to '
                       'German consumers.',
        'context': 'We surveyed over 2,000 consumers in Germany about their shopping preferences. '
                   'The results are compiled in a comprehensive report filled with engaging '
                   'infographics.',
        'pain_points': '',
        'brevo_features_tags': [   'Consumer Research',
                                   'Email Marketing',
                                   'Loyalty Programs',
                                   'Digital Loyalty Cards',
                                   'Ecommerce'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'consumer-study-2024-de-ebook-en',
        'company': 'Consumer Study 2024 (DE)',
        'title': 'Consumer Study 2024 (DE)',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/consumer-study-en-sls',
        'key_metrics': "In Brevo's 2024 survey of 2,057 German online shoppers, email ranked as "
                       'the top communication channel and digital loyalty cards emerged as a key '
                       'driver of brand loyalty — essential benchmarks for any brand selling to '
                       'German consumers.',
        'context': 'We surveyed over 2,000 consumers in Germany about their shopping preferences. '
                   'The results are compiled in a comprehensive report filled with engaging '
                   'infographics.',
        'pain_points': '',
        'brevo_features_tags': [   'Consumer Research',
                                   'Email Marketing',
                                   'Loyalty Programs',
                                   'Digital Loyalty Cards',
                                   'Ecommerce'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'corsair-case-study-case-study-de',
        'company': 'Corsair Case Study',
        'title': 'Corsair Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/de-use-case-corsair-wallet-2024-sls',
        'key_metrics': 'Corsair shows how airlines can guarantee mobile wallet marketing success — '
                       "Brevo's case study details how the airline used Wallet to strengthen "
                       'passenger engagement and loyalty.',
        'context': 'Why did Corsair choose the Wallet?\n'
                   'During a period marked by severe restrictions in the tourism industry, the '
                   'airline Corsair has been innovating to make life easier for its customers. '
                   'Corsair has therefore partnered with Brevo Wallet to offer its customers the '
                   'option of digitizing their boarding pass in their Wallet:',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Airlines/Travel',
                                   'Loyalty Programs',
                                   'Push Notifications'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'cosmetics-industry-case-study-case-study-de',
        'company': 'Cosmetics industry Case Study',
        'title': 'Cosmetics industry Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-use-case-kosmetik-wallet-2024-sls',
        'key_metrics': "See how a mobile wallet loyalty card turns cosmetics shoppers' phones into "
                       'a direct, always-on marketing channel for personalized offers and points '
                       'tracking.',
        'context': 'How the mobile wallet can be used in the cosmetics industry:\n'
                   'Based on specific examples, you will learn how brands can use the mobile '
                   'wallet to create a personalized and enriching customer experience by '
                   'integrating it into their mobile marketing strategy',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Programs', 'Marketing Automation'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'coupon-network-catalina-case-study-fr',
        'company': 'Coupon Network (Catalina)',
        'title': 'Coupon Network (Catalina)',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/coupon-network-fr',
        'key_metrics': "Coupon Network's 1M+ users save up to €180/month and redeem 380+ coupons a "
                       "year thanks to Brevo's push-first Email + Push orchestration strategy.",
        'context': '1. Master Summary\n'
                   'Coupon Network (Catalina), an app and website with 1M+ users that helps '
                   'consumers save on their favorite brands (up to €180/month and 380+ '
                   'coupons/year), runs a push-first engagement strategy powered by Brevo. Push '
                   'notifications act as the primary activation channel for time-sensitive moments '
                   '(offers, challenges, reminders, expirations), with email as a supporting '
                   'channel for detailed information and backup reach. Behavior-triggered, '
                   'personalized push notifications significantly outperform generic scheduled '
                   'sends, and the switch from a legacy tool to Brevo cut deployment time in half '
                   'while doubling the number of templates in use.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — strong reference for objection handling on push '
                   'notification strategy, channel orchestration, and migration speed from a '
                   'legacy tool.\n'
                   'Ideal prospect profile: Consumer app (couponing, cashback, deals, loyalty) '
                   'where user engagement depends on time-sensitive, behavior-driven moments, '
                   'needing push as the primary channel with email as a coordinated support '
                   'channel. Also relevant for prospects migrating from a legacy/complex marketing '
                   'stack who need fast time-to-market and marketer autonomy from technical '
                   'teams.\n'
                   'Pitch: "If your app lives or dies on getting the timing right — offers, '
                   'reminders, expirations — Coupon Network is a strong reference. They built a '
                   'push-first strategy with Brevo, coordinated with email as backup, and cut '
                   'their campaign deployment time in half while doubling their template library, '
                   'all while leaving a legacy tool behind in just a few weeks."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Push-first strategy: push is the "hero channel" for immediate, actionable, '
                   'contextual moments; email is the complementary channel for detailed '
                   "information, reassurance, or backup when push isn't opened.\n"
                   '- Scenario-driven orchestration: a time-based journey triggers the right '
                   'channel depending on user reaction (e.g. welcome push+email on day 0, product '
                   'discovery email on D+7, validated-discount push on D+7, reactivation '
                   'push+email on D+30).\n'
                   '- Behavior-triggered pushes strongly outperform scheduled bulk sends and '
                   'generic content (see KPIs).\n'
                   '- Fast migration from a legacy tool: first push and email campaigns launched '
                   'within a few weeks, a velocity described as impossible with their previous '
                   'infrastructure.\n'
                   '- Marketer autonomy: an intuitive interface removed the need for constant '
                   'back-and-forth with technical teams for each campaign.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 1M+ users on the Coupon Network app; users save up to €180/month and 380+ '
                   'coupons/year.\n'
                   '- Push median time-to-open: ~7 minutes on iOS, ~48 minutes on Android.\n'
                   '- Open rate: ~8.0% for behavior-triggered pushes vs ~1.9% for scheduled bulk '
                   'sends (behavior-triggered performs ~4x better). Benchmark source: Leanplum '
                   "report (1.5B messages), relayed by Marketing Dive — not Coupon Network's own "
                   'figures.\n'
                   '- Open rate: ~5.9% for personalized pushes vs ~1.5% for generic pushes.\n'
                   '- Welcome journey example: 29% open rate, 3.3% CTR across the push+email '
                   'welcome/offer/reminder sequence.\n'
                   '- Since switching to Brevo: number of templates in use doubled (20 today vs 2 '
                   'before Brevo); campaign deployment speed halved (2x productivity); 97% email '
                   'deliverability rate over the past year.\n'
                   '- Quote: “We needed to leave our old tool quickly. With Brevo, onboarding was '
                   'so intuitive that our teams were operational almost immediately, without any '
                   'drop in performance.” — Laura Michel, Growth Lead at Catalina.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'push notifications, push-first, mobile engagement, couponing, cashback, coupon '
                   'app, behavior-triggered automation, personalization, channel orchestration, '
                   'push vs email, deliverability, legacy migration, time-to-market, marketer '
                   'autonomy, no-code campaigns, retail, ecommerce, loyalty, wallet, Brevo '
                   'Automation, Brevo Push, Catalina, Coupon Network, Leanplum benchmark, open '
                   'rate benchmark, CTR',
        'pain_points': '',
        'brevo_features_tags': ['Push Notifications', 'Email Marketing', 'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Network', 'Feature Specialist']},
    {   'id': 'coyote-success-story-fr',
        'company': 'Coyote',
        'title': 'Coyote',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'tech_saas',
        'url': 'https://www.brevo.com/fr/resources/coyote-success-story/',
        'key_metrics': 'This French connected-driver-safety pioneer (5M+ community members) '
                       "replaced Adobe Campaign with Brevo's CDP and Marketing Automation to "
                       'orchestrate Email, SMS, WhatsApp, and Push across 5 European markets from '
                       'one multi-account architecture.',
        'context': '1. Master Summary\n'
                   'Coyote, pioneer of connected driver assistance services in France with 5M+ '
                   'community members, replaced its legacy Adobe Campaign infrastructure with '
                   'Brevo to orchestrate its omnichannel marketing across 5 European markets '
                   "(France, Benelux, Spain, Italy, UK). Built on Brevo's CDP and a multi-account "
                   'architecture, the setup unifies community data and activates Email, SMS, '
                   'WhatsApp, Push, and transactional API in real time. The result: an '
                   'industrialized, personalized engagement engine capable of operating at '
                   'European scale without sacrificing the community-first experience that defines '
                   "Coyote's brand.\n"
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo, Proposal — ideal for objection handling on '
                   'scale, platform migration (especially Adobe Campaign), and multi-country '
                   'architecture.\n'
                   'Ideal prospect profile: Large B2C or community-driven enterprise managing '
                   'millions of contacts across multiple markets, looking to consolidate their '
                   'martech stack and replace a legacy platform with a more agile, sovereign '
                   'solution. Relevant sectors: tech, mobility, connected services, media.\n'
                   'Pitch: "You\'re managing millions of contacts across several countries with a '
                   "legacy platform that's become too rigid and costly — that's exactly what "
                   'Coyote solved by migrating from Adobe Campaign to Brevo, with a multi-account '
                   'CDP architecture and a full omnichannel stack running across 5 European '
                   'markets."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '• Migration from Adobe Campaign to Brevo: demonstrates viability for '
                   'enterprise clients on legacy platforms seeking agility and sovereignty.\n'
                   '• Multi-account architecture: separate accounts per market (France, Benelux, '
                   'Spain, Italy, UK) enabling local customization at scale.\n'
                   '• Full omnichannel activation: Email, SMS, WhatsApp, Push (in-app), and '
                   'transactional API all orchestrated from one platform.\n'
                   '• Proactive retention use case: automated scenario targeting subscribers '
                   'approaching their 3rd month of usage, combining Push + SMS for critical '
                   'touchpoints.\n'
                   '• AI-powered optimization and real-time routing: right channel, right moment, '
                   'for millions of users.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '• Community size: 5M+ members\n'
                   '• Geographic scope: 5 European markets (France, Benelux, Spain, Italy, UK)\n'
                   '• Previous platform: Adobe Campaign (migration story)\n'
                   '• Channels activated: Email, SMS, WhatsApp, Push (in-app), Transactional API\n'
                   'No ROI or performance metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'Adobe Campaign migration, CDP, customer data platform, multi-account, '
                   'omnichannel, marketing automation, email, SMS, WhatsApp, push notifications, '
                   'transactional API, community marketing, retention, Europe, multi-country, '
                   'connected services, mobility, tech, enterprise, Brevo CDP, Brevo Enterprise, '
                   'data unification, segmentation, real-time routing, AI optimization, '
                   'large-scale CRM, Kundenbindung, Omnichannel-Marketing, fidélisation '
                   'communauté, migration Adobe Campaign, marketing omnicanal, architecture '
                   'multi-comptes',
        'pain_points': '',
        'brevo_features_tags': [   'Customer Data Platform (CDP)',
                                   'Marketing Automation',
                                   'Multi-Account Architecture',
                                   'Transactional Email API',
                                   'Omnichannel (Email/SMS/WhatsApp/Push)'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Network', 'Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': '4-successful-crm-strategies-for-german-smbs-ebook-de',
        'company': '4 successful CRM strategies for German SMBs',
        'title': 'DE ebook: 4 successful CRM strategies for German SMBs',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-mittelstand-de-sls',
        'key_metrics': 'A practical playbook for German Mittelstand teams: scale marketing '
                       'automation, lift customer lifetime value, unify data with a CDP, and go '
                       'multichannel — without adding headcount.',
        'context': 'This DE ebook shows how a CRM system can help SMBs overcome their biggest '
                   'marketing challenges and offers concrete solutions. The following 4 topics are '
                   'examined in more detail: Scaling marketing processes and personalizing '
                   'customer communications at scale, increasing customer loyalty (including '
                   'loyalty programs), consolidating customer data using a CDP, and creating '
                   'successful multichannel campaigns. It is enriched with a few success stories. '
                   'Recommended usage: Sales follow-up, field & growth marketing promotions & '
                   'nurturing content',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Customer Data Platform (CDP)',
                                   'Multichannel Marketing',
                                   'Customer Retention'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Graduate', 'Network', 'Consolidator']},
    {   'id': 'coding-loyalty-programs-ebook-ebook-fr',
        'company': 'coding Loyalty Programs Ebook',
        'title': 'Decoding Loyalty Programs Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-decryptage-programmes-fidelite-fr-sls',
        'key_metrics': '87% of consumers are already enrolled in at least one loyalty program, '
                       'averaging 6 programs per person (Brevo x IFOP 2024 barometer) — see what '
                       'makes a program actually stand out.',
        'context': 'Loyalty benefits and latest trends.\n'
                   'The different types of loyalty programs: a comprehensive analysis of over 250 '
                   'customers.\n'
                   'Our advice and concrete examples for your loyalty strategy.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Mobile Wallet',
                                   'Customer Data Platform (CDP)'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'coding-loyalty-programs-ebook-ebook-de',
        'company': 'coding Loyalty Programs Ebook',
        'title': 'Decoding Loyalty Programs Ebook',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-alles-ueber-treueprogramme-2024-sls',
        'key_metrics': '87% of consumers are already enrolled in at least one loyalty program, '
                       'averaging 6 programs per person (Brevo x IFOP 2024 barometer) — see what '
                       'makes a program actually stand out.',
        'context': 'Loyalty benefits and latest trends.\n'
                   'The different types of loyalty programs: a comprehensive analysis of over 250 '
                   'customers.\n'
                   'Our advice and concrete examples for your loyalty strategy.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Mobile Wallet',
                                   'Customer Data Platform (CDP)'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'coding-loyalty-programs-ebook-ebook-en',
        'company': 'coding Loyalty Programs Ebook',
        'title': 'Decoding Loyalty Programs Ebook',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/decoding-loyalty-2024-sls',
        'key_metrics': '87% of consumers are already enrolled in at least one loyalty program, '
                       'averaging 6 programs per person (Brevo x IFOP 2024 barometer) — see what '
                       'makes a program actually stand out.',
        'context': 'Loyalty benefits and latest trends.\n'
                   'The different types of loyalty programs: a comprehensive analysis of over 250 '
                   'customers.\n'
                   'Our advice and concrete examples for your loyalty strategy.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Mobile Wallet',
                                   'Customer Data Platform (CDP)'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'doctolib-case-study-case-study-fr',
        'company': 'Doctolib Case Study',
        'title': 'Doctolib Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/Doctolib-Succes-Story-FR-sls',
        'key_metrics': 'Doctolib relies on Brevo to send up to 130M transactional emails a month '
                       'with millions of simultaneous API calls, without losing a beat even at '
                       'peak traffic.',
        'context': 'Doctolib teamed up with Brevo to tackle the challenge of managing a growing '
                   'number of transactional emails while keeping everything secure and compliant '
                   'with healthcare regulations. With Brevo’s API and real-time tools, they nailed '
                   'email deliverability, kept everything running smoothly, and stayed on top of '
                   'GDPR requirements. This partnership shows how Brevo helped Doctolib send '
                   'millions of emails every month, stay secure, and make life easier for both '
                   'patients and healthcare providers.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email Deliverability',
                                   'API Integration',
                                   'Marketing Automation'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-case-study-case-study-en',
        'company': 'Doctolib Case Study',
        'title': 'Doctolib Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/Doctolib-case-study-0125-sls',
        'key_metrics': 'Doctolib relies on Brevo to send up to 130M transactional emails a month '
                       'with millions of simultaneous API calls, without losing a beat even at '
                       'peak traffic.',
        'context': 'Doctolib teamed up with Brevo to tackle the challenge of managing a growing '
                   'number of transactional emails while keeping everything secure and compliant '
                   'with healthcare regulations. With Brevo’s API and real-time tools, they nailed '
                   'email deliverability, kept everything running smoothly, and stayed on top of '
                   'GDPR requirements. This partnership shows how Brevo helped Doctolib send '
                   'millions of emails every month, stay secure, and make life easier for both '
                   'patients and healthcare providers.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email Deliverability',
                                   'API Integration',
                                   'Marketing Automation'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-case-study-case-study-de',
        'company': 'Doctolib Case Study',
        'title': 'Doctolib Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/doctolib-case-study-de-sls',
        'key_metrics': 'Doctolib relies on Brevo to send up to 130M transactional emails a month '
                       'with millions of simultaneous API calls, without losing a beat even at '
                       'peak traffic.',
        'context': 'Doctolib teamed up with Brevo to tackle the challenge of managing a growing '
                   'number of transactional emails while keeping everything secure and compliant '
                   'with healthcare regulations. With Brevo’s API and real-time tools, they nailed '
                   'email deliverability, kept everything running smoothly, and stayed on top of '
                   'GDPR requirements. This partnership shows how Brevo helped Doctolib send '
                   'millions of emails every month, stay secure, and make life easier for both '
                   'patients and healthcare providers.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email Deliverability',
                                   'API Integration',
                                   'Marketing Automation'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-onepager-case-study-fr',
        'company': 'Doctolib Onepager',
        'title': 'Doctolib Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'health',
        'url': 'https://content.brevo.com/onepager-doctolib-fr-sls',
        'key_metrics': 'Doctolib sends 75M transactional emails a month through Brevo at 99% '
                       'deliverability, 0.2% hard bounce, and 600ms delivery time for its most '
                       'urgent messages.',
        'context': 'Discover how Doctolib uses Brevo to optimize transactional emails on a one '
                   'page.',
        'pain_points': '',
        'brevo_features_tags': ['Transactional Email', 'Email Deliverability', 'API Integration'],
        'best_for_verticals': ['health'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-onepager-case-study-en',
        'company': 'Doctolib Onepager',
        'title': 'Doctolib Onepager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'health',
        'url': 'https://content.brevo.com/onepager-doctolib-en-sls',
        'key_metrics': 'Doctolib sends 75M transactional emails a month through Brevo at 99% '
                       'deliverability, 0.2% hard bounce, and 600ms delivery time for its most '
                       'urgent messages.',
        'context': 'Discover how Doctolib uses Brevo to optimize transactional emails on a one '
                   'page.',
        'pain_points': '',
        'brevo_features_tags': ['Transactional Email', 'Email Deliverability', 'API Integration'],
        'best_for_verticals': ['health'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-onepager-case-study-de',
        'company': 'Doctolib Onepager',
        'title': 'Doctolib Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'health',
        'url': 'https://content.brevo.com/onepager-doctolib-de-sls',
        'key_metrics': 'Doctolib sends 75M transactional emails a month through Brevo at 99% '
                       'deliverability, 0.2% hard bounce, and 600ms delivery time for its most '
                       'urgent messages.',
        'context': 'Discover how Doctolib uses Brevo to optimize transactional emails on a one '
                   'page.',
        'pain_points': '',
        'brevo_features_tags': ['Transactional Email', 'Email Deliverability', 'API Integration'],
        'best_for_verticals': ['health'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'doctolib-onepager-case-study-es',
        'company': 'Doctolib Onepager',
        'title': 'Doctolib Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'health',
        'url': 'https://content.brevo.com/onepager-doctolib-es-sls',
        'key_metrics': 'Doctolib sends 75M transactional emails a month through Brevo at 99% '
                       'deliverability, 0.2% hard bounce, and 600ms delivery time for its most '
                       'urgent messages.',
        'context': 'Discover how Doctolib uses Brevo to optimize transactional emails on a one '
                   'page.',
        'pain_points': '',
        'brevo_features_tags': ['Transactional Email', 'Email Deliverability', 'API Integration'],
        'best_for_verticals': ['health'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': '5-customer-success-stories-boost-engagement-multiply-your-re',
        'company': '5 Customer Success Stories : “Boost Engagement & Multiply Your Revenue”',
        'title': 'Ebook - 5 Customer Success Stories : “Boost Engagement & Multiply Your Revenue”',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/5-success-stories-fr',
        'key_metrics': 'Maison 123 doubled its average basket size with a mobile wallet-powered '
                       'loyalty program — one of 5 real client playbooks inside for boosting '
                       'engagement and revenue.',
        'context': 'Master summary: This compilation decodes five concrete customer success '
                   'stories, detailing how brands like Maison 123, Lacoste, Alltricks, Oliviers & '
                   'Co, and Feu Vert used Brevo to transform their customer engagement and '
                   'multiply revenue. It provides practical, replicable strategies for modernizing '
                   'loyalty programs, leveraging AI for smart segmentation, and unifying data '
                   'through a Customer Data Platform (CDP).\n'
                   'Best use / When to share: Share during the Consideration or Decision stages '
                   'with marketing leaders, CRM managers, and E-commerce directors looking for '
                   'proven ROI. This asset is ideal for overcoming skepticism about platform '
                   'impact, as it addresses common pain points like rigid legacy loyalty systems, '
                   'mass-mailing fatigue, scattered customer data, and the struggle to create true '
                   'omnichannel personalization.\n'
                   'Key takeaways:\n'
                   '• Maison 123: Replaced a paper loyalty card with a Mobile Wallet, resulting in '
                   'a 99% retention rate, doubled purchase frequency, and a 36.5x ROI.\n'
                   '• Lacoste: Evolved from a transactional points system to an engagement-driven '
                   'loyalty program ("Lacoste Members") leveraging gamification, co-creation, and '
                   'VIP tiers to generate over 150 community projects.\n'
                   '• Alltricks: Moved from mass mailing to dynamic segmentation and predictive AI '
                   'targeting, expanding their relevant audience while doubling their '
                   'click-through rates and recovering abandoned carts via web push.\n'
                   '• Oliviers & Co: Solved the challenge of fragmented online/offline data (50 '
                   'boutiques, 70% franchisees) by unifying customer data with a CDP, increasing '
                   'web revenue by 14%.\n'
                   '• Feu Vert: Addressed complex personalization needs by utilizing "custom '
                   'objects" to tailor communications based on specific vehicle data, rather than '
                   'generic customer profiles.\n'
                   'Search keywords: success stories, case studies, customer stories, revenue '
                   'multiplication, customer engagement, Maison 123, Lacoste, Alltricks, Oliviers '
                   '& Co, Feu Vert, mobile wallet, loyalty program, gamification, predictive AI, '
                   'dynamic segmentation, CDP, custom objects, omnichannel personalization, '
                   'e-commerce, retail\n'
                   'Notes & Status: Contains five detailed customer use cases spanning retail and '
                   'e-commerce. No explicit publication date is provided, but references to '
                   "Brevo's CDP and advanced custom objects indicate recent, Enterprise-focused "
                   'capabilities.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Email Marketing',
                                   'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '5-customer-success-stories-boost-engagement-multiply-your-re-2',
        'company': '5 Customer Success Stories : “Boost Engagement & Multiply Your Revenue”',
        'title': 'Ebook - 5 Customer Success Stories : “Boost Engagement & Multiply Your Revenue”',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/5-success-stories',
        'key_metrics': 'Maison 123 doubled its average basket size with a mobile wallet-powered '
                       'loyalty program — one of 5 real client playbooks inside for boosting '
                       'engagement and revenue.',
        'context': 'Master summary: This compilation decodes five concrete customer success '
                   'stories, detailing how brands like Maison 123, Lacoste, Alltricks, Oliviers & '
                   'Co, and Feu Vert used Brevo to transform their customer engagement and '
                   'multiply revenue. It provides practical, replicable strategies for modernizing '
                   'loyalty programs, leveraging AI for smart segmentation, and unifying data '
                   'through a Customer Data Platform (CDP).\n'
                   'Best use / When to share: Share during the Consideration or Decision stages '
                   'with marketing leaders, CRM managers, and E-commerce directors looking for '
                   'proven ROI. This asset is ideal for overcoming skepticism about platform '
                   'impact, as it addresses common pain points like rigid legacy loyalty systems, '
                   'mass-mailing fatigue, scattered customer data, and the struggle to create true '
                   'omnichannel personalization.\n'
                   'Key takeaways:\n'
                   '• Maison 123: Replaced a paper loyalty card with a Mobile Wallet, resulting in '
                   'a 99% retention rate, doubled purchase frequency, and a 36.5x ROI.\n'
                   '• Lacoste: Evolved from a transactional points system to an engagement-driven '
                   'loyalty program ("Lacoste Members") leveraging gamification, co-creation, and '
                   'VIP tiers to generate over 150 community projects.\n'
                   '• Alltricks: Moved from mass mailing to dynamic segmentation and predictive AI '
                   'targeting, expanding their relevant audience while doubling their '
                   'click-through rates and recovering abandoned carts via web push.\n'
                   '• Oliviers & Co: Solved the challenge of fragmented online/offline data (50 '
                   'boutiques, 70% franchisees) by unifying customer data with a CDP, increasing '
                   'web revenue by 14%.\n'
                   '• Feu Vert: Addressed complex personalization needs by utilizing "custom '
                   'objects" to tailor communications based on specific vehicle data, rather than '
                   'generic customer profiles.\n'
                   'Search keywords: success stories, case studies, customer stories, revenue '
                   'multiplication, customer engagement, Maison 123, Lacoste, Alltricks, Oliviers '
                   '& Co, Feu Vert, mobile wallet, loyalty program, gamification, predictive AI, '
                   'dynamic segmentation, CDP, custom objects, omnichannel personalization, '
                   'e-commerce, retail\n'
                   'Notes & Status: Contains five detailed customer use cases spanning retail and '
                   'e-commerce. No explicit publication date is provided, but references to '
                   "Brevo's CDP and advanced custom objects indicate recent, Enterprise-focused "
                   'capabilities.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Email Marketing',
                                   'Marketing Automation'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '7-customer-success-stories-row-case-study-en',
        'company': '7 Customer Success Stories RoW',
        'title': 'eBook - 7 Customer Success Stories RoW',
        'type': 'case_study',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/EN-Success-Stories-RoW-eBook-sls',
        'key_metrics': 'Great British Chefs lifted email open rates by 10% using dynamic contact '
                       'segmentation — one of 7 real customer success stories inside from across '
                       'industries.',
        'context': 'This eBook delves into how 7 RoW companies overcame challenges, enhanced '
                   'customer engagement, and achieved exceptional growth. Each case study provides '
                   'practical insights and strategies, offering valuable lessons for driving '
                   'success in a competitive market.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing', 'Contact Segmentation', 'Marketing Automation'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': '7-customer-success-stories-us-case-study-en',
        'company': '7 Customer Success Stories US',
        'title': 'eBook - 7 Customer Success Stories US',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'fintech',
        'url': 'https://content.brevo.com/EN-Success-Stories-US-eBook',
        'key_metrics': 'Island Federal Credit Union hit 80% email open rates by automating its '
                       'email program — one of 7 US customer success stories inside spanning '
                       'finance, media, and B2B.',
        'context': 'This eBook delves into how 7 US companies overcame challenges, enhanced '
                   'customer engagement, and achieved exceptional growth. Each case study provides '
                   'practical insights and strategies, offering valuable lessons for driving '
                   'success in a competitive market.',
        'pain_points': '',
        'brevo_features_tags': ['Email Marketing Automation', 'Email Deliverability'],
        'best_for_verticals': [   'fintech',
                                  'entertainment',
                                  'media_publishing',
                                  'education',
                                  'tech_saas',
                                  'b2b_services'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': '6-customer-success-stories-dach-case-study-de',
        'company': '6 Customer Success Stories - DACH',
        'title': 'eBook 6 Customer Success Stories - DACH',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/success-stories-dach-sls',
        'key_metrics': 'Trusted Shops reactivated 21% of its dormant contacts with Brevo — one of '
                       "6 DACH success stories inside, including Burda Style's multi-account "
                       'marketing overhaul.',
        'context': 'This eBook delves into how 6 DACH companies overcame challenges, enhanced '
                   'customer engagement, and achieved exceptional growth. Each case study provides '
                   'practical insights and strategies, offering valuable lessons for driving '
                   'success in a competitive market.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Contact Reactivation',
                                   'Multi-Account Management',
                                   'Marketing Automation'],
        'best_for_verticals': ['ecommerce', 'retail', 'media_publishing', 'tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'how-to-measure-and-optimize-the-roi-of-your-loyalty-program-',
        'company': 'How to measure and optimize the ROI of your loyalty program',
        'title': 'Ebook : How to measure and optimize the ROI of your loyalty program',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-mesurer-roi-loyalty-fr-sls',
        'key_metrics': 'This ebook hands you the exact formula to prove loyalty program ROI — in '
                       'the worked example, a €15M program investment nets a 100% return.',
        'context': 'This ebook will help you calculate and optimize the ROI of your loyalty '
                   "programs. You'll discover calculation methods, performance evaluation and "
                   'forecasting tools, as well as concrete examples of successful programs.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Programs', 'Analytics & Reporting', 'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'how-to-measure-and-optimize-the-roi-of-your-loyalty-program--2',
        'company': 'How to measure and optimize the ROI of your loyalty program',
        'title': 'Ebook : How to measure and optimize the ROI of your loyalty program',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-ROI-treueprogramm-messen-optimieren-sls',
        'key_metrics': 'This ebook hands you the exact formula to prove loyalty program ROI — in '
                       'the worked example, a €15M program investment nets a 100% return.',
        'context': 'This ebook will help you calculate and optimize the ROI of your loyalty '
                   "programs. You'll discover calculation methods, performance evaluation and "
                   'forecasting tools, as well as concrete examples of successful programs.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Programs', 'Analytics & Reporting', 'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'how-to-measure-and-optimize-the-roi-of-your-loyalty-program--3',
        'company': 'How to measure and optimize the ROI of your loyalty program',
        'title': 'Ebook : How to measure and optimize the ROI of your loyalty program',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-loyalty-roi-en-sls',
        'key_metrics': 'This ebook hands you the exact formula to prove loyalty program ROI — in '
                       'the worked example, a €15M program investment nets a 100% return.',
        'context': 'This ebook will help you calculate and optimize the ROI of your loyalty '
                   "programs. You'll discover calculation methods, performance evaluation and "
                   'forecasting tools, as well as concrete examples of successful programs.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Programs', 'Analytics & Reporting', 'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': '5-crm-strategies-for-media-industry-ebook-de',
        'company': '5 CRM strategies for media industry',
        'title': 'Ebook: 5 CRM strategies for media industry',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/ebook-crm-media-de-2024-sls',
        'key_metrics': '5 CRM plays built specifically for publishers and media companies — from '
                       'AI-powered content personalization to CDP-driven data integration — to '
                       'grow subscriber and advertiser relationships.',
        'context': 'This ebook explores the benefits for media companies and publishers to '
                   'implement a reliable CRM solution, effective use cases and 5 successful CRM '
                   'tactics and best practices for both subscription business and advertising '
                   'sales. It is enriched with success stories and features quotes from an '
                   'industry expert who is a DE ENT client. Recommended usage: Sales follow-up, '
                   'field & growth marketing promotions & nurturing content',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'AI Content Personalization',
                                   'Customer Data Platform (CDP)',
                                   'Multichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Network', 'Consolidator']},
    {   'id': '5-crm-strategies-for-media-industry-ebook-en',
        'company': '5 CRM strategies for media industry',
        'title': 'Ebook: 5 CRM strategies for media industry',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/ebook-crm-media-en-2024-sls',
        'key_metrics': '5 CRM plays built specifically for publishers and media companies — from '
                       'AI-powered content personalization to CDP-driven data integration — to '
                       'grow subscriber and advertiser relationships.',
        'context': 'This ebook explores the benefits for media companies and publishers to '
                   'implement a reliable CRM solution, effective use cases and 5 successful CRM '
                   'tactics and best practices for both subscription business and advertising '
                   'sales. It is enriched with success stories and features quotes from an '
                   'industry expert who is a DE ENT client. Recommended usage: Sales follow-up, '
                   'field & growth marketing promotions & nurturing content',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'AI Content Personalization',
                                   'Customer Data Platform (CDP)',
                                   'Multichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Network', 'Consolidator']},
    {   'id': '5-crm-strategies-for-media-industry-ebook-fr',
        'company': '5 CRM strategies for media industry',
        'title': 'Ebook: 5 CRM strategies for media industry',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/ebook-crm-media-fr-2024-sls',
        'key_metrics': '5 CRM plays built specifically for publishers and media companies — from '
                       'AI-powered content personalization to CDP-driven data integration — to '
                       'grow subscriber and advertiser relationships.',
        'context': 'This ebook explores the benefits for media companies and publishers to '
                   'implement a reliable CRM solution, effective use cases and 5 successful CRM '
                   'tactics and best practices for both subscription business and advertising '
                   'sales. It is enriched with success stories and features quotes from an '
                   'industry expert who is a DE ENT client. Recommended usage: Sales follow-up, '
                   'field & growth marketing promotions & nurturing content',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'AI Content Personalization',
                                   'Customer Data Platform (CDP)',
                                   'Multichannel Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Network', 'Consolidator']},
    {   'id': 'enterprise-vs-self-service-comparison-ebook-en',
        'company': 'Enterprise vs Self-Service Comparison',
        'title': 'Ebook: Enterprise vs Self-Service Comparison',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ent-ss-comp-ebook-en-sls',
        'key_metrics': 'See exactly what upgrading unlocks: centralized multi-account management, '
                       'a scalable loyalty engine, and a dedicated success manager, mapped '
                       'head-to-head against self-service.',
        'context': 'Detailed comparison of the Business and Enterprise plans',
        'pain_points': '',
        'brevo_features_tags': [   'Enterprise Plan',
                                   'Loyalty Programs',
                                   'Customer Success',
                                   'Multi-Account Management',
                                   'Marketing Automation'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Graduate', 'Network', 'Feature Specialist']},
    {   'id': 'enterprise-vs-self-service-comparison-ebook-de',
        'company': 'Enterprise vs Self-Service Comparison',
        'title': 'Ebook: Enterprise vs Self-Service Comparison',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/ent-vs-ss-comparison-de',
        'key_metrics': 'See exactly what upgrading unlocks: centralized multi-account management, '
                       'a scalable loyalty engine, and a dedicated success manager, mapped '
                       'head-to-head against self-service.',
        'context': 'Detailed comparison of the Business and Enterprise plans',
        'pain_points': '',
        'brevo_features_tags': [   'Enterprise Plan',
                                   'Loyalty Programs',
                                   'Customer Success',
                                   'Multi-Account Management',
                                   'Marketing Automation'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Graduate', 'Network', 'Feature Specialist']},
    {   'id': 'elevating-your-media-or-publishing-business-with-digital-mar',
        'company': 'Elevating your media or publishing business with digital marketing',
        'title': 'Elevating your media or publishing business with digital marketing',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://corp-backend.brevo.com/wp-content/uploads/2023/06/Digital-Marketing-for-Media-_-Publishing-EN.pdf',
        'key_metrics': 'A digital marketing playbook for media and publishing brands on delivering '
                       'limitless content personalization across email, SMS, and chat to keep '
                       'audiences engaged.',
        'context': 'A digital marketing playbook for media and publishing brands on delivering '
                   'limitless content personalization across email, SMS, and chat to keep '
                   'audiences engaged.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'SMS Marketing',
                                   'Live Chat',
                                   'Personalization',
                                   'Media & Publishing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'email-marketing-for-consumer-packaged-goods-ebook-en',
        'company': 'Email Marketing for Consumer Packaged Goods',
        'title': 'Email Marketing for Consumer Packaged Goods',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://corp-backend.brevo.com/wp-content/uploads/2023/06/email-marketing-for-retail-and-cpg-EN.pdf',
        'key_metrics': 'A retail and CPG-focused email marketing playbook covering everything from '
                       'campaign fundamentals to advanced personalization and deliverability, '
                       'aimed at driving greater customer loyalty.',
        'context': 'A retail and CPG-focused email marketing playbook covering everything from '
                   'campaign fundamentals to advanced personalization and deliverability, aimed at '
                   'driving greater customer loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Deliverability',
                                   'Retail & CPG'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'email-marketing-for-consumer-packaged-goods-ebook-fr',
        'company': 'Email Marketing for Consumer Packaged Goods',
        'title': 'Email Marketing for Consumer Packaged Goods',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'http://corp-backend.brevo.com/fr/wp-content/uploads/sites/4/2023/06/email-marketing-for-retail-and-cpg-FR.pdf',
        'key_metrics': 'A retail and CPG-focused email marketing playbook covering everything from '
                       'campaign fundamentals to advanced personalization and deliverability, '
                       'aimed at driving greater customer loyalty.',
        'context': 'A retail and CPG-focused email marketing playbook covering everything from '
                   'campaign fundamentals to advanced personalization and deliverability, aimed at '
                   'driving greater customer loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Deliverability',
                                   'Retail & CPG'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'email-marketing-for-consumer-packaged-goods-ebook-de',
        'company': 'Email Marketing for Consumer Packaged Goods',
        'title': 'Email Marketing for Consumer Packaged Goods',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'retail',
        'url': 'http://corp-backend.brevo.com/de/wp-content/uploads/sites/5/2023/06/email-marketing-for-retail-and-cpg-DE.pdf',
        'key_metrics': 'A retail and CPG-focused email marketing playbook covering everything from '
                       'campaign fundamentals to advanced personalization and deliverability, '
                       'aimed at driving greater customer loyalty.',
        'context': 'A retail and CPG-focused email marketing playbook covering everything from '
                   'campaign fundamentals to advanced personalization and deliverability, aimed at '
                   'driving greater customer loyalty.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Deliverability',
                                   'Retail & CPG'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'faq-ebook-the-mobile-wallet-for-your-brand-ebook-de',
        'company': 'FAQ Ebook: The Mobile Wallet for your Brand',
        'title': 'FAQ Ebook: The Mobile Wallet for your Brand',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-for-your-brand-2024-sls',
        'key_metrics': "Brevo's Mobile Wallet already lives on 24 million active cards across "
                       'Europe with a 90% average customer retention rate and covers 35% of '
                       'smartphones in France — proof this channel has serious reach.',
        'context': 'This ebook gives answers to the most frequently asked questions. \n'
                   'How is the wallet used internationally?\n'
                   'For which scenarios or use cases can the wallet be used?\n'
                   'In which areas can the wallet be used?\n'
                   'Can I design the wallet cards in the colors of my brand?',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Cards',
                                   'Customer Retention',
                                   'Digital Marketing'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'faq-ebook-the-mobile-wallet-for-your-budget-objectives-ebook',
        'company': 'FAQ Ebook: The Mobile Wallet for your budget & objectives',
        'title': 'FAQ Ebook: The Mobile Wallet for your budget & objectives',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-for-your-budget-2024-sls',
        'key_metrics': 'One Brevo client measured a 36.5% ROI and a 3% lift in total revenue from '
                       'the Mobile Wallet, with customers who add the card spending 45% more on '
                       'average and buying 30% more often.',
        'context': 'In this format, we answer the most important questions about the mobile wallet '
                   'in terms of budget and strategy.\n'
                   'How is ROI calculated with the mobile wallet?\n'
                   'What is the ROI for our customers?\n'
                   'What are the advantages for our customers beyond ROI?\n'
                   'What are the costs?',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'ROI Measurement', 'Customer Loyalty', 'CRM'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'faq-ebook-the-mobile-wallet-for-your-clients-ebook-de',
        'company': 'FAQ Ebook: The Mobile Wallet for your clients',
        'title': 'FAQ Ebook: The Mobile Wallet for your clients',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-for-your-clients-2024-sls',
        'key_metrics': "Even among 55+ customers, brands using Brevo's Mobile Wallet see 2x higher "
                       'purchase frequency and 2x more revenue per customer than non-wallet users '
                       "— this isn't just a channel for younger audiences.",
        'context': 'In this format, we answer the most important questions about the mobile wallet '
                   'in relation to your customers.\n'
                   'Which age group is the wallet aimed at?\n'
                   'How can my customers use the wallet? etc.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Customer Engagement',
                                   'Insurance',
                                   'Loyalty Cards'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'tech_saas',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'faq-ebook-the-mobile-wallet-for-your-strategy-ebook-de',
        'company': 'FAQ Ebook: The Mobile Wallet for your strategy',
        'title': 'FAQ Ebook: The Mobile Wallet for your strategy',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-for-your-strategy-2024-sls',
        'key_metrics': "70% of marketing emails go unseen and SMS feels intrusive — Brevo's Mobile "
                       'Wallet reaches customers in just two taps on the one screen they check '
                       'daily: their smartphone lock screen.',
        'context': 'In this format, we answer the most important questions about the mobile wallet '
                   'in relation to your strategy. What impact does it have and how can it '
                   'positively influence your strategy?\n'
                   'I already use many different marketing channels.\n'
                   "I don't have my own loyalty program, can I still use the Brevo Wallet? I "
                   "already offer my own app, what's the point of the mobile wallet?\n"
                   'What advantage does the wallet offer compared to frequently used channels such '
                   'as email or SMS?\n'
                   'How does the solution help me improve the customer experience?\n'
                   'How can I integrate the mobile wallet into my omnichannel strategy?',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Email Marketing',
                                   'SMS Marketing',
                                   'Push Notifications'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'entertainment'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'faq-ebook-the-mobile-wallet-for-your-teams-ebook-de',
        'company': 'FAQ Ebook: The Mobile Wallet for your teams',
        'title': 'FAQ Ebook: The Mobile Wallet for your teams',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-for-your-teams-2024-sls',
        'key_metrics': "Brevo's Mobile Wallet launches in just 6-8 weeks with almost zero IT lift "
                       '— no API endpoints required, just a short technical workshop and a few '
                       'days of setup.',
        'context': 'In this format, we answer the most important questions about the Mobile Wallet '
                   'in terms of its impact on your teams.\n'
                   'Here are the questions and objections we address in this white paper:\n'
                   "• I don't have the capacity and can't involve my IT team.\n"
                   '• How long will it take before I can use the Mobile Wallet for my marketing '
                   'strategy?',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Implementation',
                                   'IT Integration',
                                   'Loyalty Cards'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'figaro-classifieds-case-study-fr',
        'company': 'Figaro Classifieds',
        'title': 'Figaro Classifieds',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/figaro-classifieds-case-study-fr-sls',
        'key_metrics': 'Figaro Classifieds scaled transactional email volume from 100M to 200M '
                       'sends a month while maintaining 99.38% deliverability, after fully '
                       'migrating off Sendgrid onto Brevo.',
        'context': 'French online classifieds leader Figaro Classifieds successfully migrated to '
                   'Brevo to absorb an additional 136 million emails per month across its top '
                   'brands, including Cadremploi. Through tailored IP warm-up plans, Brevo enabled '
                   'them to seamlessly manage complex volume flows and massive daily peaks (up to '
                   '3.5M emails/day) while maintaining top-tier deliverability.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email Deliverability',
                                   'Email API',
                                   'Marketing Automation'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist', 'Saver']},
    {   'id': 'figaro-classifieds-case-study-de',
        'company': 'Figaro Classifieds',
        'title': 'Figaro Classifieds',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/figaro-classifieds-case-study-de-sls',
        'key_metrics': 'Figaro Classifieds scaled transactional email volume from 100M to 200M '
                       'sends a month while maintaining 99.38% deliverability, after fully '
                       'migrating off Sendgrid onto Brevo.',
        'context': 'French online classifieds leader Figaro Classifieds successfully migrated to '
                   'Brevo to absorb an additional 136 million emails per month across its top '
                   'brands, including Cadremploi. Through tailored IP warm-up plans, Brevo enabled '
                   'them to seamlessly manage complex volume flows and massive daily peaks (up to '
                   '3.5M emails/day) while maintaining top-tier deliverability.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email Deliverability',
                                   'Email API',
                                   'Marketing Automation'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist', 'Saver']},
    {   'id': 'florida-trend-achieves-50-open-rate-by-leveraging-dynamic-co',
        'company': 'Florida Trend Achieves 50% Open Rate by Leveraging Dynamic Contact '
                   'Segmentation',
        'title': 'Florida Trend Achieves 50% Open Rate by Leveraging Dynamic Contact Segmentation',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://www.brevo.com/success-stories/florida-trend/',
        'key_metrics': 'This 25-person publisher scaled from 2M to 3M+ emails/month without a '
                       'pricing penalty, and now consistently beats a 20% base open rate -- with '
                       'some newsletters topping 50% open rate.',
        'context': 'This 25-person publisher scaled from 2M to 3M+ emails/month without a pricing '
                   'penalty, and now consistently beats a 20% base open rate -- with some '
                   'newsletters topping 50% open rate.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Campaigns',
                                   'Dynamic Contact Segmentation',
                                   'Enterprise Plan',
                                   'Campaign Reporting & Analytics',
                                   'Dedicated CSM'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator']},
    {   'id': 'fnac-darty-success-story-fr',
        'company': 'Fnac Darty',
        'title': 'Fnac Darty',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://www.brevo.com/fr/resources/fnac-darty-success-story/',
        'key_metrics': "Europe's leading omnichannel retailer (30,000+ employees, 1,500 stores) "
                       'called their Brevo SSO rollout "one of the fastest production rollouts in '
                       'our history" -- letting business teams run campaigns autonomously while IT '
                       'keeps centralized identity and access control.',
        'context': "Fnac Darty successfully implemented Brevo's SSO in record time, proving that "
                   'enterprise-grade security and marketing agility can perfectly coexist. This '
                   'seamless integration allowed their IT team to maintain strict access control '
                   '(IAM) while ensuring fast, widespread adoption by the business teams.',
        'pain_points': '',
        'brevo_features_tags': [   'Single Sign-On (SSO)',
                                   'Identity & Access Management (IAM) Integration',
                                   'Enterprise Security',
                                   'SaaS Configuration Autonomy'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'fnac-darty-success-story-en',
        'company': 'Fnac Darty',
        'title': 'Fnac Darty',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://www.brevo.com/resources/fnac-darty-success-story/',
        'key_metrics': "Europe's leading omnichannel retailer (30,000+ employees, 1,500 stores) "
                       'called their Brevo SSO rollout "one of the fastest production rollouts in '
                       'our history" -- letting business teams run campaigns autonomously while IT '
                       'keeps centralized identity and access control.',
        'context': "Fnac Darty successfully implemented Brevo's SSO in record time, proving that "
                   'enterprise-grade security and marketing agility can perfectly coexist. This '
                   'seamless integration allowed their IT team to maintain strict access control '
                   '(IAM) while ensuring fast, widespread adoption by the business teams.',
        'pain_points': '',
        'brevo_features_tags': [   'Single Sign-On (SSO)',
                                   'Identity & Access Management (IAM) Integration',
                                   'Enterprise Security',
                                   'SaaS Configuration Autonomy'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'food-hospitality-industry-case-study-case-study-de',
        'company': 'Food/Hospitality industry Case Study',
        'title': 'Food/Hospitality industry Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-use-case-gastronomie-wallet-2024-sls',
        'key_metrics': "See how brands like McDonald's, KFC, and Buffalo Grill turn receipts and "
                       'reservation confirmations into a one-tap loyalty card in the Mobile Wallet '
                       '— no app download required.',
        'context': 'How the mobile wallet can be used in the hospitality/food industry:\n'
                   'Using specific examples, you will learn how restaurants can offer their guests '
                   'a more personal and enriching experience by integrating the mobile wallet into '
                   'their marketing strategy.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Cards',
                                   'Restaurant & Hospitality Marketing',
                                   'Click & Collect'],
        'best_for_verticals': ['ecommerce', 'hospitality'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'gaining-a-competitive-edge-with-conversational-marketing-for',
        'company': 'Gaining a competitive edge with conversational marketing for retailers',
        'title': 'Gaining a competitive edge with conversational marketing for retailers',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://corp-backend.brevo.com/wp-content/uploads/2023/06/conversational-marketing-for-retail-and-cpg.pdf',
        'key_metrics': 'A conversational marketing playbook showing retailers how to gain a '
                       'competitive edge by meeting shoppers where they are -- via chat, '
                       'messaging, and real-time engagement.',
        'context': 'A conversational marketing playbook showing retailers how to gain a '
                   'competitive edge by meeting shoppers where they are -- via chat, messaging, '
                   'and real-time engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Conversational Marketing',
                                   'Live Chat/Chatbot',
                                   'Retail & CPG',
                                   'Customer Engagement'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'great-british-chefs-increases-email-open-rates-by-10-using-d',
        'company': 'Great British Chefs Increases Email Open Rates by 10% Using Dynamic Contact '
                   'Segmentation',
        'title': 'Great British Chefs Increases Email Open Rates by 10% Using Dynamic Contact '
                 'Segmentation',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://www.brevo.com/success-stories/great-british-chefs/',
        'key_metrics': 'This 9-person UK media team lifted open rates from 25% to 35% (+10pts) and '
                       'cut subscriber drop-off -- using dynamic segmentation layered on their '
                       'existing Shopify + membership stack.',
        'context': 'This 9-person UK media team lifted open rates from 25% to 35% (+10pts) and cut '
                   'subscriber drop-off -- using dynamic segmentation layered on their existing '
                   'Shopify + membership stack.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Campaigns',
                                   'Dynamic Contact Segmentation',
                                   'Marketing Automation (welcome journeys)',
                                   'Transactional Email',
                                   'Shopify Integration',
                                   'Lead Scoring (planned)'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'great-british-chefs-increases-email-open-rates-by-10-using-d-2',
        'company': 'Great British Chefs Increases Email Open Rates by 10% Using Dynamic Contact '
                   'Segmentation',
        'title': 'Great British Chefs Increases Email Open Rates by 10% Using Dynamic Contact '
                 'Segmentation',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://www.brevo.com/de/success-stories/great-british-chefs/',
        'key_metrics': 'This 9-person UK media team lifted open rates from 25% to 35% (+10pts) and '
                       'cut subscriber drop-off -- using dynamic segmentation layered on their '
                       'existing Shopify + membership stack.',
        'context': 'This 9-person UK media team lifted open rates from 25% to 35% (+10pts) and cut '
                   'subscriber drop-off -- using dynamic segmentation layered on their existing '
                   'Shopify + membership stack.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Campaigns',
                                   'Dynamic Contact Segmentation',
                                   'Marketing Automation (welcome journeys)',
                                   'Transactional Email',
                                   'Shopify Integration',
                                   'Lead Scoring (planned)'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'how-to-build-customer-loyalty-5-effective-strategies-with-th',
        'company': 'How to build customer loyalty: 5 effective strategies with the wallet',
        'title': 'How to build customer loyalty: 5 effective strategies with the wallet',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-5-strategien-kundentreue-mobile-wallet-sls',
        'key_metrics': 'Loyal customers spend 67% more than new ones, and the top 20% of a '
                       'customer base can drive up to 80% of revenue — this guide shows 5 ways '
                       "Brevo's Mobile Wallet turns that loyalty into a lasting channel.",
        'context': 'Customer loyalty is a key element in ensuring the growth and longevity of your '
                   'business. By adopting the effective strategies with the mobile wallet '
                   'described in this white paper, you can transform your customers into true '
                   'ambassadors of your brand.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Customer Loyalty',
                                   'Loyalty Programs',
                                   'Personalization'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'how-to-build-customer-loyalty-5-effective-strategies-with-th-2',
        'company': 'How to build customer loyalty: 5 effective strategies with the wallet',
        'title': 'How to build customer loyalty: 5 effective strategies with the wallet',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/ebook-5-strategies-wallet-fr-sls',
        'key_metrics': 'Loyal customers spend 67% more than new ones, and the top 20% of a '
                       'customer base can drive up to 80% of revenue — this guide shows 5 ways '
                       "Brevo's Mobile Wallet turns that loyalty into a lasting channel.",
        'context': 'Customer loyalty is a key element in ensuring the growth and longevity of your '
                   'business. By adopting the effective strategies with the mobile wallet '
                   'described in this white paper, you can transform your customers into true '
                   'ambassadors of your brand.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Customer Loyalty',
                                   'Loyalty Programs',
                                   'Personalization'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'imerys-success-story-fr',
        'company': 'Imerys',
        'title': 'Imerys',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'industrial',
        'url': 'https://www.brevo.com/fr/resources/imerys-success-story/',
        'key_metrics': 'This global mining/materials group scaled from 10 to 120+ active Brevo '
                       'users and structured 14 sub-accounts across countries -- holding ~98.5% '
                       'average deliverability while auto-syncing 140+ Google Groups into Brevo '
                       'contact lists daily.',
        'context': '1. Master Summary\n'
                   'Imerys, a global industrial minerals group operating across multiple '
                   "countries, uses Brevo's multi-account (sub-account) solution to govern "
                   'internal communications at scale. Each business unit or country operates its '
                   'own isolated Brevo sub-account, managed centrally from a parent admin account. '
                   'The case demonstrates how a global enterprise can standardize and control '
                   'multi-country communications without sacrificing local autonomy, while '
                   'progressively extending the platform to external marketing use cases.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Project Exploration, Technical Validation — ideal for '
                   'enterprise prospects with multiple BUs, countries, or brands needing '
                   'centralized governance with local autonomy.\n'
                   'Ideal prospect profile: Global enterprise (industry, manufacturing, B2B '
                   'services) with decentralized marketing teams across countries or divisions, '
                   'needing to manage email communications at scale with data isolation, billing '
                   'consolidation, and admin oversight. Also relevant for agencies managing '
                   'multiple client accounts.\n'
                   'Pitch: "If you\'re managing communications across multiple countries or '
                   'business units and struggling to keep data isolated while maintaining central '
                   "oversight — Imerys is a great reference. They use Brevo's multi-account "
                   'architecture to govern communications globally from a single admin, with each '
                   'entity working independently in its own environment."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Multi-account architecture for global governance: sub-accounts per '
                   'BU/country, fully isolated, managed from one parent admin.\n'
                   '- Central control + local autonomy: admin manages billing, credits, and '
                   'permissions; each sub-account operates independently.\n'
                   "- Internal communications use case: demonstrates Brevo's relevance beyond "
                   'marketing — internal newsletters, HR communications, operational alerts.\n'
                   '- Progressive expansion to external marketing: the platform serves as a '
                   'foundation that scales from internal to customer-facing use.\n'
                   '- Enterprise-grade data isolation: each sub-account has separate contact '
                   'lists, API keys, and sending infrastructure.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '> No specific KPIs or figures available — the asset description does not '
                   'include performance metrics.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'multi-account, sub-accounts, sous-comptes, global enterprise, multi-country, '
                   'decentralized, governance, internal communications, B2B, industry, '
                   'manufacturing, admin account, data isolation, billing consolidation, Brevo '
                   'Enterprise, multi-BU, brand management, operational efficiency, IT governance, '
                   'Imerys, minéraux industriels, communications internes, architecture '
                   'multi-comptes, Mehrkontoverwaltung, Unternehmenskommunikation, '
                   'Datenisolierung, enterprise governance',
        'pain_points': '',
        'brevo_features_tags': [   'Multi-Account / Sub-Account Management',
                                   'Email Deliverability',
                                   'Automated Contact Sync',
                                   'Enterprise Governance'],
        'best_for_verticals': ['industrial'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Network', 'Email Specialist']},
    {   'id': 'jacadi-onepager-case-study-fr',
        'company': 'Jacadi Onepager',
        'title': 'Jacadi Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/Onepager-Jacadi-sls',
        'key_metrics': 'Jacadi saw a 39% jump in purchase frequency and 23% higher revenue per '
                       "client after moving its loyalty card into Brevo's Mobile Wallet, with 97% "
                       "of the card's usage happening on mobile.",
        'context': 'Discover how Jacadi makes its communications ultra-personal with the mobile '
                   'wallet.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Programs',
                                   'Push Notifications',
                                   'Retail & Fashion Marketing'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'jurafuchs-success-story-en',
        'company': 'Jurafuchs',
        'title': 'Jurafuchs',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'education',
        'url': 'https://www.brevo.com/resources/jurafuchs-success-story/',
        'key_metrics': "Germany's #1 legal-education app scaled to 25,000+ monthly active users "
                       'and 150,000 emails/month on Brevo -- powering onboarding automation, '
                       'spaced-repetition retention emails, event-driven workflows (via '
                       'Fullstory), and free-to-paid conversion campaigns.',
        'context': '1. Master Summary\n'
                   'Jurafuchs, a leading German EdTech app with 25,000+ monthly active users '
                   "helping law students prepare for their exams, uses Brevo's event-driven email "
                   'automations and Fullstory integration to scale three critical lifecycle '
                   'moments: user onboarding, daily retention, and freemium-to-premium upsell. By '
                   'connecting behavioral data (in-app events) to automated email triggers, '
                   'Jurafuchs delivers hyper-relevant communications at exactly the right moment '
                   'in the learning journey — without manual intervention.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — ideal for SaaS, app, or EdTech prospects '
                   'looking to automate lifecycle communications based on product usage data.\n'
                   'Ideal prospect profile: B2C SaaS or mobile app company (EdTech, productivity, '
                   'subscription) with a freemium model, looking to automate onboarding sequences, '
                   'reduce churn, and convert free users to paid via behavioral email triggers. '
                   'Relevant for German-speaking market prospects.\n'
                   'Pitch: "If you have a freemium product and your onboarding or upsell emails '
                   'are still manual or based on fixed timers rather than actual user behavior — '
                   "Jurafuchs shows what's possible: event-driven automations connected to in-app "
                   'usage data via Fullstory, triggering the right email at the exact moment a '
                   'user needs a nudge."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Event-driven automation: email triggers based on real in-app user behavior '
                   '(via Fullstory integration), not just time-based sequences.\n'
                   '- Three lifecycle use cases in one platform: onboarding, daily retention, and '
                   'freemium-to-premium upsell — all automated.\n'
                   '- Fullstory x Brevo integration: a strong technical proof point for '
                   'product-led growth companies using session analytics tools.\n'
                   '- Scalable without headcount: 25K+ MAU managed with lean marketing automation, '
                   'no manual sending.\n'
                   '- German market reference: valuable for DACH-market EdTech or SaaS prospects.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 25,000+ monthly active users (MAU)\n'
                   '- Channels: Email, Push Notifications, Transactional API\n'
                   '- Integration: Fullstory\n'
                   'No open rate, conversion, or revenue metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'EdTech, SaaS, freemium, upsell, onboarding, retention, event-driven '
                   'automation, behavioral triggers, Fullstory, integration, push notifications, '
                   'transactional email, API, lifecycle marketing, DACH, Germany, law students, '
                   'mobile app, product-led growth, Brevo Automation, Brevo API, 25K MAU, '
                   'subscription, churn reduction, Lern-App, Onboarding-Automatisierung, '
                   'Freemium-Upgrade, Nutzerverhalten, EdTech Deutschland, automatisation '
                   'comportementale, rétention utilisateurs, upsell freemium',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Event-Driven Workflows',
                                   'Transactional Email',
                                   'Onboarding Automation',
                                   'Conversion Campaigns',
                                   'Fullstory Integration'],
        'best_for_verticals': ['education'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist']},
    {   'id': 'jurafuchs-success-story-fr',
        'company': 'Jurafuchs',
        'title': 'Jurafuchs',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'education',
        'url': 'https://www.brevo.com/fr/resources/jurafuchs-success-story/',
        'key_metrics': "Germany's #1 legal-education app scaled to 25,000+ monthly active users "
                       'and 150,000 emails/month on Brevo -- powering onboarding automation, '
                       'spaced-repetition retention emails, event-driven workflows (via '
                       'Fullstory), and free-to-paid conversion campaigns.',
        'context': '1. Master Summary\n'
                   'Jurafuchs, a leading German EdTech app with 25,000+ monthly active users '
                   "helping law students prepare for their exams, uses Brevo's event-driven email "
                   'automations and Fullstory integration to scale three critical lifecycle '
                   'moments: user onboarding, daily retention, and freemium-to-premium upsell. By '
                   'connecting behavioral data (in-app events) to automated email triggers, '
                   'Jurafuchs delivers hyper-relevant communications at exactly the right moment '
                   'in the learning journey — without manual intervention.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — ideal for SaaS, app, or EdTech prospects '
                   'looking to automate lifecycle communications based on product usage data.\n'
                   'Ideal prospect profile: B2C SaaS or mobile app company (EdTech, productivity, '
                   'subscription) with a freemium model, looking to automate onboarding sequences, '
                   'reduce churn, and convert free users to paid via behavioral email triggers. '
                   'Relevant for German-speaking market prospects.\n'
                   'Pitch: "If you have a freemium product and your onboarding or upsell emails '
                   'are still manual or based on fixed timers rather than actual user behavior — '
                   "Jurafuchs shows what's possible: event-driven automations connected to in-app "
                   'usage data via Fullstory, triggering the right email at the exact moment a '
                   'user needs a nudge."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Event-driven automation: email triggers based on real in-app user behavior '
                   '(via Fullstory integration), not just time-based sequences.\n'
                   '- Three lifecycle use cases in one platform: onboarding, daily retention, and '
                   'freemium-to-premium upsell — all automated.\n'
                   '- Fullstory x Brevo integration: a strong technical proof point for '
                   'product-led growth companies using session analytics tools.\n'
                   '- Scalable without headcount: 25K+ MAU managed with lean marketing automation, '
                   'no manual sending.\n'
                   '- German market reference: valuable for DACH-market EdTech or SaaS prospects.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 25,000+ monthly active users (MAU)\n'
                   '- Channels: Email, Push Notifications, Transactional API\n'
                   '- Integration: Fullstory\n'
                   'No open rate, conversion, or revenue metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'EdTech, SaaS, freemium, upsell, onboarding, retention, event-driven '
                   'automation, behavioral triggers, Fullstory, integration, push notifications, '
                   'transactional email, API, lifecycle marketing, DACH, Germany, law students, '
                   'mobile app, product-led growth, Brevo Automation, Brevo API, 25K MAU, '
                   'subscription, churn reduction, Lern-App, Onboarding-Automatisierung, '
                   'Freemium-Upgrade, Nutzerverhalten, EdTech Deutschland, automatisation '
                   'comportementale, rétention utilisateurs, upsell freemium',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Event-Driven Workflows',
                                   'Transactional Email',
                                   'Onboarding Automation',
                                   'Conversion Campaigns',
                                   'Fullstory Integration'],
        'best_for_verticals': ['education'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist']},
    {   'id': 'kenya-airways-success-story-fr',
        'company': 'Kenya Airways',
        'title': 'Kenya Airways',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'transportation',
        'url': 'https://www.brevo.com/fr/resources/kenya-airways-success-story/',
        'key_metrics': 'Kenya Airways grew its Asante Rewards loyalty program membership by 70% in '
                       "just 10 months, sending 300K-400K transactional emails/month via Brevo's "
                       'Email API -- with plans to expand into the full Marketing Platform for '
                       'segmentation and automation.',
        'context': 'Discover how the airline ensures a seamless member experience for thousands of '
                   'new monthly sign-ups using Brevo’s sending infrastructure.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email API',
                                   'Loyalty Program Infrastructure',
                                   'High-Volume Sending Reliability',
                                   'Marketing Platform (planned)'],
        'best_for_verticals': ['transportation'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'kenya-airways-success-story-en',
        'company': 'Kenya Airways',
        'title': 'Kenya Airways',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'transportation',
        'url': 'https://www.brevo.com/en/resources/kenya-airways-success-story/',
        'key_metrics': 'Kenya Airways grew its Asante Rewards loyalty program membership by 70% in '
                       "just 10 months, sending 300K-400K transactional emails/month via Brevo's "
                       'Email API -- with plans to expand into the full Marketing Platform for '
                       'segmentation and automation.',
        'context': 'Discover how the airline ensures a seamless member experience for thousands of '
                   'new monthly sign-ups using Brevo’s sending infrastructure.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email API',
                                   'Loyalty Program Infrastructure',
                                   'High-Volume Sending Reliability',
                                   'Marketing Platform (planned)'],
        'best_for_verticals': ['transportation'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'les-bougies-de-charroux-success-story-fr',
        'company': 'Les Bougies de Charroux',
        'title': 'Les Bougies de Charroux',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://www.brevo.com/fr/resources/les-bougies-de-charroux-success-story/',
        'key_metrics': 'This French artisan candle brand unified its online store (Shopify Plus) '
                       'and in-store POS (Cegid Retail Y2) into one gamified loyalty program -- '
                       'rewarding customers with "flames" for purchases AND social actions '
                       '(unboxing videos, TikTok follows), for a full 360-degree customer view.',
        'context': '1. Master Summary\n'
                   'Les Bougies de Charroux, a French artisan candle brand with both physical '
                   'stores and an online presence, deployed a gamified omnichannel loyalty program '
                   'with Brevo — "Le Cercle d\'Aurore" — connecting their Shopify Plus e-commerce '
                   'to their in-store POS system Cegid Retail Y2. The program rewards purchases '
                   'through a branded "flames" mechanic and integrates social challenges '
                   '(unboxing, brand film, TikTok follow) to turn loyal customers into active '
                   'brand ambassadors. The result: a unified 360° customer view across web and '
                   'physical, and a community engaged well beyond the point of purchase.\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, demo, proposal — especially for objection handling '
                   'around the complexity of unifying physical and digital channels.\n'
                   'Ideal prospect profile: SMB or mid-market retail/e-commerce with an '
                   'omnichannel presence (store + website), using Shopify or a similar e-commerce '
                   'platform paired with a POS system, looking to go beyond a standard '
                   'transactional loyalty program. Relevant sectors: lifestyle, artisan goods, '
                   'beauty, home.\n'
                   '"You\'re trying to build loyalty across your store and your website without '
                   'managing two separate silos — Les Bougies de Charroux solved exactly that with '
                   'Brevo: a program running in real time between their Cegid POS and Shopify, '
                   'with a gamification layer that gets customers talking about the brand on '
                   'social media."\n'
                   '3. Key Takeaways\n'
                   '• Native omnichannel integration: seamless Shopify Plus ↔ Cegid Retail Y2 '
                   'connection, giving sales teams a unified 360° customer view.\n'
                   '• Differentiated loyalty mechanics: a branded "flames" currency (consistent '
                   'with the brand universe) rather than a generic points system.\n'
                   '• Social gamification: 3 challenges (unboxing video, brand film viewing, '
                   'TikTok follow) to reward community engagement and drive organic brand '
                   'visibility.\n'
                   '• Day-one activation: 50-flame signup bonus to encourage immediate program '
                   'adoption.\n'
                   '• From transaction to community: the program positions Brevo Loyalty as a '
                   'brand advocacy engine, not just a retention tool.\n'
                   '4. Key KPIs, Figures & InsightsNo specific KPIs or figures are included in '
                   'this asset. The page describes the solution and mechanics deployed but does '
                   'not publish any performance metrics (adoption rate, revenue growth, number of '
                   'members, social engagement, etc.).\n'
                   '5. Search Keywords\n'
                   'omnichannel loyalty, loyalty program, gamification, loyalty mechanics, flames, '
                   'Wallet, Brevo Loyalty, Shopify Plus, Cegid Retail, omnichannel, retail, '
                   'e-commerce, physical store, brand ambassador, brand advocacy, social '
                   'challenges, TikTok, unboxing, community engagement, artisan, lifestyle, home, '
                   'SMB, mid-market, 360° customer view, customer retention, rewards program, '
                   'cross-channel loyalty, case study loyalty, success story loyalty, '
                   'Kundenbindung, Omnichannel-Loyalität, fidélité omnicanale, programme de '
                   'fidélité, gamification, fidélisation client',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty & Rewards Platform',
                                   'Omnichannel POS/Ecommerce Integration (Shopify Plus, Cegid)',
                                   'Gamification',
                                   'Social Engagement Features'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'les-bougies-de-charroux-success-story-en',
        'company': 'Les Bougies de Charroux',
        'title': 'Les Bougies de Charroux',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://www.brevo.com/resources/les-bougies-de-charroux-success-story/',
        'key_metrics': 'This French artisan candle brand unified its online store (Shopify Plus) '
                       'and in-store POS (Cegid Retail Y2) into one gamified loyalty program -- '
                       'rewarding customers with "flames" for purchases AND social actions '
                       '(unboxing videos, TikTok follows), for a full 360-degree customer view.',
        'context': '1. Master Summary\n'
                   'Les Bougies de Charroux, a French artisan candle brand with both physical '
                   'stores and an online presence, deployed a gamified omnichannel loyalty program '
                   'with Brevo — "Le Cercle d\'Aurore" — connecting their Shopify Plus e-commerce '
                   'to their in-store POS system Cegid Retail Y2. The program rewards purchases '
                   'through a branded "flames" mechanic and integrates social challenges '
                   '(unboxing, brand film, TikTok follow) to turn loyal customers into active '
                   'brand ambassadors. The result: a unified 360° customer view across web and '
                   'physical, and a community engaged well beyond the point of purchase.\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, demo, proposal — especially for objection handling '
                   'around the complexity of unifying physical and digital channels.\n'
                   'Ideal prospect profile: SMB or mid-market retail/e-commerce with an '
                   'omnichannel presence (store + website), using Shopify or a similar e-commerce '
                   'platform paired with a POS system, looking to go beyond a standard '
                   'transactional loyalty program. Relevant sectors: lifestyle, artisan goods, '
                   'beauty, home.\n'
                   '"You\'re trying to build loyalty across your store and your website without '
                   'managing two separate silos — Les Bougies de Charroux solved exactly that with '
                   'Brevo: a program running in real time between their Cegid POS and Shopify, '
                   'with a gamification layer that gets customers talking about the brand on '
                   'social media."\n'
                   '3. Key Takeaways\n'
                   '• Native omnichannel integration: seamless Shopify Plus ↔ Cegid Retail Y2 '
                   'connection, giving sales teams a unified 360° customer view.\n'
                   '• Differentiated loyalty mechanics: a branded "flames" currency (consistent '
                   'with the brand universe) rather than a generic points system.\n'
                   '• Social gamification: 3 challenges (unboxing video, brand film viewing, '
                   'TikTok follow) to reward community engagement and drive organic brand '
                   'visibility.\n'
                   '• Day-one activation: 50-flame signup bonus to encourage immediate program '
                   'adoption.\n'
                   '• From transaction to community: the program positions Brevo Loyalty as a '
                   'brand advocacy engine, not just a retention tool.\n'
                   '4. Key KPIs, Figures & InsightsNo specific KPIs or figures are included in '
                   'this asset. The page describes the solution and mechanics deployed but does '
                   'not publish any performance metrics (adoption rate, revenue growth, number of '
                   'members, social engagement, etc.).\n'
                   '5. Search Keywords\n'
                   'omnichannel loyalty, loyalty program, gamification, loyalty mechanics, flames, '
                   'Wallet, Brevo Loyalty, Shopify Plus, Cegid Retail, omnichannel, retail, '
                   'e-commerce, physical store, brand ambassador, brand advocacy, social '
                   'challenges, TikTok, unboxing, community engagement, artisan, lifestyle, home, '
                   'SMB, mid-market, 360° customer view, customer retention, rewards program, '
                   'cross-channel loyalty, case study loyalty, success story loyalty, '
                   'Kundenbindung, Omnichannel-Loyalität, fidélité omnicanale, programme de '
                   'fidélité, gamification, fidélisation client',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty & Rewards Platform',
                                   'Omnichannel POS/Ecommerce Integration (Shopify Plus, Cegid)',
                                   'Gamification',
                                   'Social Engagement Features'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'les-bougies-de-charroux-success-story-de',
        'company': 'Les Bougies de Charroux',
        'title': 'Les Bougies de Charroux',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://www.brevo.com/de/resources/les-bougies-de-charroux-success-story/',
        'key_metrics': 'This French artisan candle brand unified its online store (Shopify Plus) '
                       'and in-store POS (Cegid Retail Y2) into one gamified loyalty program -- '
                       'rewarding customers with "flames" for purchases AND social actions '
                       '(unboxing videos, TikTok follows), for a full 360-degree customer view.',
        'context': '1. Master Summary\n'
                   'Les Bougies de Charroux, a French artisan candle brand with both physical '
                   'stores and an online presence, deployed a gamified omnichannel loyalty program '
                   'with Brevo — "Le Cercle d\'Aurore" — connecting their Shopify Plus e-commerce '
                   'to their in-store POS system Cegid Retail Y2. The program rewards purchases '
                   'through a branded "flames" mechanic and integrates social challenges '
                   '(unboxing, brand film, TikTok follow) to turn loyal customers into active '
                   'brand ambassadors. The result: a unified 360° customer view across web and '
                   'physical, and a community engaged well beyond the point of purchase.\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, demo, proposal — especially for objection handling '
                   'around the complexity of unifying physical and digital channels.\n'
                   'Ideal prospect profile: SMB or mid-market retail/e-commerce with an '
                   'omnichannel presence (store + website), using Shopify or a similar e-commerce '
                   'platform paired with a POS system, looking to go beyond a standard '
                   'transactional loyalty program. Relevant sectors: lifestyle, artisan goods, '
                   'beauty, home.\n'
                   '"You\'re trying to build loyalty across your store and your website without '
                   'managing two separate silos — Les Bougies de Charroux solved exactly that with '
                   'Brevo: a program running in real time between their Cegid POS and Shopify, '
                   'with a gamification layer that gets customers talking about the brand on '
                   'social media."\n'
                   '3. Key Takeaways\n'
                   '• Native omnichannel integration: seamless Shopify Plus ↔ Cegid Retail Y2 '
                   'connection, giving sales teams a unified 360° customer view.\n'
                   '• Differentiated loyalty mechanics: a branded "flames" currency (consistent '
                   'with the brand universe) rather than a generic points system.\n'
                   '• Social gamification: 3 challenges (unboxing video, brand film viewing, '
                   'TikTok follow) to reward community engagement and drive organic brand '
                   'visibility.\n'
                   '• Day-one activation: 50-flame signup bonus to encourage immediate program '
                   'adoption.\n'
                   '• From transaction to community: the program positions Brevo Loyalty as a '
                   'brand advocacy engine, not just a retention tool.\n'
                   '4. Key KPIs, Figures & InsightsNo specific KPIs or figures are included in '
                   'this asset. The page describes the solution and mechanics deployed but does '
                   'not publish any performance metrics (adoption rate, revenue growth, number of '
                   'members, social engagement, etc.).\n'
                   '5. Search Keywords\n'
                   'omnichannel loyalty, loyalty program, gamification, loyalty mechanics, flames, '
                   'Wallet, Brevo Loyalty, Shopify Plus, Cegid Retail, omnichannel, retail, '
                   'e-commerce, physical store, brand ambassador, brand advocacy, social '
                   'challenges, TikTok, unboxing, community engagement, artisan, lifestyle, home, '
                   'SMB, mid-market, 360° customer view, customer retention, rewards program, '
                   'cross-channel loyalty, case study loyalty, success story loyalty, '
                   'Kundenbindung, Omnichannel-Loyalität, fidélité omnicanale, programme de '
                   'fidélité, gamification, fidélisation client',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty & Rewards Platform',
                                   'Omnichannel POS/Ecommerce Integration (Shopify Plus, Cegid)',
                                   'Gamification',
                                   'Social Engagement Features'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'liligo-onepager-case-study-fr',
        'company': 'Liligo Onepager',
        'title': 'Liligo Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/case-study-liligo-2-fr-sls',
        'key_metrics': 'Liligo drives 90% of its CRM-generated revenue from real-time price '
                       'alerts, sending up to 250k emails a day and bursting to 120k emails a '
                       "minute via Brevo's email API without sacrificing deliverability.",
        'context': 'Discover how Liligo uses Brevo to send millions of personalized price alerts '
                   'in real time, in a one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email API',
                                   'Email Deliverability',
                                   'Travel Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'liligo-onepager-case-study-de',
        'company': 'Liligo Onepager',
        'title': 'Liligo Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/onepager-liligo-de-sls',
        'key_metrics': 'Liligo drives 90% of its CRM-generated revenue from real-time price '
                       'alerts, sending up to 250k emails a day and bursting to 120k emails a '
                       "minute via Brevo's email API without sacrificing deliverability.",
        'context': 'Discover how Liligo uses Brevo to send millions of personalized price alerts '
                   'in real time, in a one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email API',
                                   'Email Deliverability',
                                   'Travel Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'liligo-onepager-case-study-es',
        'company': 'Liligo Onepager',
        'title': 'Liligo Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'hospitality',
        'url': 'https://content.brevo.com/onepager-liligo-es-sls',
        'key_metrics': 'Liligo drives 90% of its CRM-generated revenue from real-time price '
                       'alerts, sending up to 250k emails a day and bursting to 120k emails a '
                       "minute via Brevo's email API without sacrificing deliverability.",
        'context': 'Discover how Liligo uses Brevo to send millions of personalized price alerts '
                   'in real time, in a one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Email API',
                                   'Email Deliverability',
                                   'Travel Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'locagestion-success-story-fr',
        'company': 'Locagestion',
        'title': 'Locagestion',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'b2b_services',
        'url': 'https://www.brevo.com/fr/resources/locagestion-success-story/',
        'key_metrics': 'This French property-management company now tracks 2,300+ sales '
                       "opportunities across 9 custom pipelines in Brevo's Sales CRM -- unifying "
                       'sales, marketing, and support teams with deal flow that runs automatically '
                       'from their Meetings booking tool into the CRM.',
        'context': '1. Master Summary\n'
                   'Locagestion, a major player in rental property management in France, deployed '
                   "Brevo's all-in-one platform to unify its commercial, marketing, and customer "
                   'support operations across three distinct client profiles. Using Sales CRM with '
                   'Meetings, Marketing Automation, a Chatbot for 24/7 lead qualification, and '
                   'omnichannel retention campaigns, the company now manages 2,300+ opportunities '
                   'across 9 custom pipelines. The result: a fully structured, automated '
                   'commercial cycle that bridges field teams, HQ, and customers seamlessly.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo, Proposal — ideal for prospects in professional '
                   'services or franchise networks needing to align sales pipelines with marketing '
                   'and support under one roof.\n'
                   'Ideal prospect profile: Mid-market B2B or B2C service company managing a high '
                   'volume of deals across different client segments, with distributed teams that '
                   'need to coordinate sales, marketing, and support. Sectors: real estate, '
                   'professional services, franchise networks, property management.\n'
                   'Pitch: "If you\'re managing hundreds of prospects and clients across multiple '
                   'team profiles with disconnected tools — Locagestion is a great example. They '
                   'went from fragmented operations to 2,300+ opportunities tracked across 9 '
                   'custom pipelines on Brevo, with a chatbot qualifying leads 24/7 and automated '
                   'marketing running alongside."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- 9 custom pipelines: tailored to three distinct client profiles (prospecting, '
                   "onboarding, retention), demonstrating Brevo CRM's flexibility for complex "
                   'sales organizations.\n'
                   '- 2,300+ opportunities managed: strong volume proof point for mid-market Sales '
                   'Platform use cases.\n'
                   '- Automated sales cycle: from lead capture (Meetings) to CRM entry, pipeline '
                   'progression, and follow-up — all automated.\n'
                   '- 24/7 chatbot qualification: Brevo Chatbot handles first-contact lead '
                   'qualification outside business hours, reducing manual workload.\n'
                   '- Omnichannel retention: marketing and support teams coordinate retention '
                   'campaigns using the same platform as Sales.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 2,300+ opportunities managed\n'
                   '- 9 custom pipelines\n'
                   '- Automated sales process end-to-end\n'
                   '- 24/7 lead qualification via Chatbot\n'
                   'No revenue or conversion rate metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'Sales CRM, pipeline management, real estate, property management, gestion '
                   'locative, immobilier, chatbot, lead qualification, marketing automation, '
                   'omnichannel, Meetings, professional services, franchise, distributed teams, '
                   'deal tracking, sales automation, Brevo Sales Platform, Brevo CRM, Brevo '
                   'Chatbot, B2B services, mid-market, 2300 opportunities, custom pipelines, '
                   'Immobilien CRM, Vertriebspipeline, qualification automatique, gestion des '
                   'opportunités, cycle de vente automatisé, fidélisation omnicanale',
        'pain_points': '',
        'brevo_features_tags': [   'Sales CRM & Pipelines',
                                   'Meetings (Booking Tool)',
                                   'Sales Automation',
                                   'Omnichannel Communication'],
        'best_for_verticals': ['b2b_services'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'loyalty-barometer-2024-ebook-fr',
        'company': 'Loyalty Barometer 2024',
        'title': 'Loyalty Barometer 2024',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-barometre-fidelite-fr-sls',
        'key_metrics': '87% of French consumers are enrolled in at least one brand loyalty '
                       "program, and 10% belong to more than 15 — Brevo's Loyalty Barometer 2024 "
                       '(with IFOP) breaks down what actually drives that engagement.',
        'context': 'This study, carried out in partnership with IFOP (french survey institute) '
                   'provides figures and key insights into consumer behaviour and perceptions of '
                   'loyalty programmes.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Market Research',
                                   'Consumer Insights',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-barometer-2024-ebook-en',
        'company': 'Loyalty Barometer 2024',
        'title': 'Loyalty Barometer 2024',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/loyalty-barometer-2024-en-sls',
        'key_metrics': '87% of French consumers are enrolled in at least one brand loyalty '
                       "program, and 10% belong to more than 15 — Brevo's Loyalty Barometer 2024 "
                       '(with IFOP) breaks down what actually drives that engagement.',
        'context': 'This study, carried out in partnership with IFOP (french survey institute) '
                   'provides figures and key insights into consumer behaviour and perceptions of '
                   'loyalty programmes.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Market Research',
                                   'Consumer Insights',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-barometer-2024-ebook-de',
        'company': 'Loyalty Barometer 2024',
        'title': 'Loyalty Barometer 2024',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-barometer-kundentreue-2024-sls',
        'key_metrics': '87% of French consumers are enrolled in at least one brand loyalty '
                       "program, and 10% belong to more than 15 — Brevo's Loyalty Barometer 2024 "
                       '(with IFOP) breaks down what actually drives that engagement.',
        'context': 'This study, carried out in partnership with IFOP (french survey institute) '
                   'provides figures and key insights into consumer behaviour and perceptions of '
                   'loyalty programmes.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Market Research',
                                   'Consumer Insights',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-barometer-2025-ebook-fr',
        'company': 'Loyalty Barometer 2025',
        'title': 'Loyalty Barometer 2025',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-loyalty-barometer-fr-25-sls',
        'key_metrics': 'French consumers are getting pickier about loyalty: average program '
                       'memberships dropped from 6 to 5.6 per person in a year, with 44% now '
                       "sticking to just 1-4 brands — Brevo's 2025 Loyalty Barometer maps the "
                       'shift toward quality over quantity.',
        'context': 'Master summary:\n'
                   'The "Loyalty Barometer 2025," produced by Brevo, explores French consumers\' '
                   'behaviors and perceptions regarding loyalty programs. Based on a survey of '
                   'over 1,000 respondents, this ebook highlights a shift toward more selective '
                   'program membership, the dominance of the retail/supermarket sector, and the '
                   'accelerating adoption of mobile wallets for storing loyalty cards and making '
                   'payments.\n'
                   '\n'
                   'Best use / When to share:\n'
                   'Share during the Consideration stage with French marketing leaders (CMOs, CRM '
                   'Managers, Digital Marketing Managers) in retail, e-commerce, and CPG. Use this '
                   'asset to back up claims about the growing importance of mobile wallets and '
                   'targeted retention strategies, directly addressing objections around digital '
                   'loyalty adoption rates or the ROI of investing in omnichannel loyalty tools.\n'
                   '\n'
                   'Key takeaways:\n'
                   '• 87% of French consumers are enrolled in at least one loyalty program, but '
                   'the average number of programs per person has dropped to 5.6, signaling a '
                   'shift toward "quality over quantity."\n'
                   '• Supermarkets (93%) and Fashion/Apparel (56%) dominate loyalty memberships, '
                   'driven by inflation and the search for promotions.\n'
                   '• 71% of French consumers find mobile wallets useful (+6 points from 2024), '
                   'with actual usage climbing, particularly among the 50-64 demographic.\n'
                   '• While 85% use wallets for loyalty cards, payment via wallet in physical '
                   'stores is up to 42%, showing increased integration of payment and loyalty in '
                   'the customer journey.\n'
                   '• Push notifications via wallets successfully prompt 47% of users to visit a '
                   'store or website, making it a highly effective retention channel.\n'
                   '\n'
                   'Search keywords:\n'
                   'loyalty barometer 2025, French consumers, loyalty programs, mobile wallet, '
                   'customer retention, CRM, retail, ecommerce, CPG, push notifications, customer '
                   'engagement, consumer behavior, Brevo study, survey, FR version, French, '
                   'loyalty trends\n'
                   '\n'
                   'Notes & Status:\n'
                   'The asset is fully in French (FR). This is proprietary, current 2025 Brevo '
                   'data (conducted May 2025), highly valuable for trust-building and thought '
                   'leadership in the French market.\n'
                   '\n'
                   'OLD: The 2025 Loyalty Barometer, our second annual survey conducted by Ifop '
                   "(French survey institute), examines French consumers' behaviors and "
                   'perceptions toward loyalty programs. This comprehensive study analyzes:\n'
                   '- Loyalty program membership rates\xa0across different demographics\n'
                   '- Sector-specific adoption\xa0of loyalty programs (retail, fashion, '
                   'restaurants, leisure, transportation)\n'
                   '- Consumer awareness\xa0of loyalty program benefits\n'
                   '- Mobile wallet adoption\xa0for storing digital loyalty cards\n'
                   '- Usage patterns\xa0of digital loyalty cards',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Programs', 'Market Research', 'Consumer Insights'],
        'best_for_verticals': [],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-program-trends-among-our-250-customers-ebook-fr',
        'company': 'Loyalty program trends among our 250 customers',
        'title': 'Loyalty program trends among our 250 customers',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-250-clients-analyses-fidelite-fr-sls',
        'key_metrics': '64% of the 250 Brevo customers analyzed run a loyalty program, and of '
                       'those, 90% keep it free while only 10% charge for premium tiers — see how '
                       'brands like Jacadi, SNCF, and Castorama structure theirs.',
        'context': 'Analysis on the adoption and usage of loyalty programs among our 250 '
                   'customers. The goal is to understand current trends and practices in loyalty '
                   'programs, such as differences across industries, who use paid programs, tier '
                   'systems, points, rewards…and much more.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Customer Retention',
                                   'Benchmark Data',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-program-trends-among-our-250-customers-ebook-en',
        'company': 'Loyalty program trends among our 250 customers',
        'title': 'Loyalty program trends among our 250 customers',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-benchmark-250-loyalty-programs-en-sls',
        'key_metrics': '64% of the 250 Brevo customers analyzed run a loyalty program, and of '
                       'those, 90% keep it free while only 10% charge for premium tiers — see how '
                       'brands like Jacadi, SNCF, and Castorama structure theirs.',
        'context': 'Analysis on the adoption and usage of loyalty programs among our 250 '
                   'customers. The goal is to understand current trends and practices in loyalty '
                   'programs, such as differences across industries, who use paid programs, tier '
                   'systems, points, rewards…and much more.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Customer Retention',
                                   'Benchmark Data',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'loyalty-program-trends-among-our-250-customers-ebook-de',
        'company': 'Loyalty program trends among our 250 customers',
        'title': 'Loyalty program trends among our 250 customers',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-benchmark-treueprogramme-2024-sls',
        'key_metrics': '64% of the 250 Brevo customers analyzed run a loyalty program, and of '
                       'those, 90% keep it free while only 10% charge for premium tiers — see how '
                       'brands like Jacadi, SNCF, and Castorama structure theirs.',
        'context': 'Analysis on the adoption and usage of loyalty programs among our 250 '
                   'customers. The goal is to understand current trends and practices in loyalty '
                   'programs, such as differences across industries, who use paid programs, tier '
                   'systems, points, rewards…and much more.',
        'pain_points': '',
        'brevo_features_tags': [   'Loyalty Programs',
                                   'Customer Retention',
                                   'Benchmark Data',
                                   'Mobile Wallet'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'm-comme-mutuelle-case-study-case-study-de',
        'company': 'M comme Mutuelle Case Study',
        'title': 'M comme Mutuelle Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-use-case-m-comme-mutuelle-wallet-2024-sls',
        'key_metrics': 'French health insurer M comme Mutuelle got 20% of its 160,000 members onto '
                       'its Brevo Mobile Wallet card within just 6 months, turning a compliance '
                       "requirement (France's RIA law) into a customer retention win.",
        'context': 'In this success story, you’ll see how they drove impressive results like '
                   'increased retention and higher conversion rates. Explore examples of their top '
                   'wallet campaigns and gain actionable insights to enhance customer engagement.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Customer Retention', 'Insurance/Mutuelle CRM'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'maison-123-case-study-fr',
        'company': 'Maison 123',
        'title': 'Maison 123',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/use-case-maison-123-fr',
        'key_metrics': 'French fashion retailer Maison 123 doubled revenue per customer by '
                       'digitizing its loyalty card into a Mobile Wallet pass with targeted push '
                       'notifications, ditching print for a greener, more personal channel across '
                       'its 175+ stores.',
        'context': 'To modernize their loyalty program and reduce print dependency, Maison 123 '
                   "deployed Brevo's Mobile Wallet and targeted push notifications. This digitized "
                   'approach maintained a continuous link with shoppers, achieving a 99% wallet '
                   'retention rate while doubling both purchase frequency and revenue per '
                   'customer.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Push Notifications',
                                   'Retail Marketing'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'maison-123-one-pager-case-study-fr',
        'company': 'Maison 123 One Pager',
        'title': 'Maison 123 One Pager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Onepager-Maison123FR-sls',
        'key_metrics': "Maison 123's Mobile Wallet loyalty card drove 2x purchase frequency, +3% "
                       'total revenue, and 99% card retention, for an estimated 36.5x ROI.',
        'context': 'Discover how Maison 123 multiplies its sales per customer thanks to the '
                   'wallet.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Customer Retention',
                                   'Retail Marketing'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'marketing-automation-for-b2b-ebook-en',
        'company': 'Marketing Automation for B2B',
        'title': 'Marketing Automation for B2B',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'b2b_services',
        'url': 'https://content.brevo.com/MAb2b',
        'key_metrics': 'B2B marketers relying on manual segmentation miss opportunities and send '
                       "irrelevant messaging — Brevo's B2B automation guide shows how dynamic, "
                       'real-time segments (by job title, industry, engagement level) let you '
                       'personalize outreach for entire buying groups, like CMOs vs. CTOs, without '
                       'the manual grind.',
        'context': 'Another version of the Marketing Automation ebook - now specific for B2B '
                   'organizations',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Segmentation',
                                   'CDP',
                                   'B2B Marketing'],
        'best_for_verticals': ['b2b_services'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'marketing-automation-for-b2b-ebook-de',
        'company': 'Marketing Automation for B2B',
        'title': 'Marketing Automation for B2B',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'b2b_services',
        'url': 'https://content.brevo.com/de-marketing-automation-b2b-2025-sls',
        'key_metrics': 'B2B marketers relying on manual segmentation miss opportunities and send '
                       "irrelevant messaging — Brevo's B2B automation guide shows how dynamic, "
                       'real-time segments (by job title, industry, engagement level) let you '
                       'personalize outreach for entire buying groups, like CMOs vs. CTOs, without '
                       'the manual grind.',
        'context': 'Another version of the Marketing Automation ebook - now specific for B2B '
                   'organizations',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Segmentation',
                                   'CDP',
                                   'B2B Marketing'],
        'best_for_verticals': ['b2b_services'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'marketing-automation-for-b2b-ebook-fr',
        'company': 'Marketing Automation for B2B',
        'title': 'Marketing Automation for B2B',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'b2b_services',
        'url': 'https://content.brevo.com/fr-marketin-automation-ebook-b2b-sls',
        'key_metrics': 'B2B marketers relying on manual segmentation miss opportunities and send '
                       "irrelevant messaging — Brevo's B2B automation guide shows how dynamic, "
                       'real-time segments (by job title, industry, engagement level) let you '
                       'personalize outreach for entire buying groups, like CMOs vs. CTOs, without '
                       'the manual grind.',
        'context': 'Another version of the Marketing Automation ebook - now specific for B2B '
                   'organizations',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Segmentation',
                                   'CDP',
                                   'B2B Marketing'],
        'best_for_verticals': ['b2b_services'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'mobile-marketing-a-catalyst-for-growth-ebook-en',
        'company': 'Mobile Marketing: A Catalyst for Growth',
        'title': 'Mobile Marketing: A Catalyst for Growth',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/MobileMarketing-Ebook-sls',
        'key_metrics': "96.5% of internet users go online via their phone — Brevo's mobile "
                       'marketing guide breaks down how SMS, push, wallet passes, and WhatsApp '
                       'each drive reach, engagement, and conversions across e-commerce, gaming, '
                       'and media.',
        'context': 'Master summary:\n'
                   'The "Mobile Marketing: A Catalyst for Growth" ebook provides a comprehensive '
                   'guide to expanding brand reach and driving engagement across mobile channels. '
                   'It breaks down the unique advantages, statistics, and industry-specific use '
                   'cases for SMS, Push Notifications, Digital Wallet, and WhatsApp marketing, '
                   'culminating in actionable strategies to integrate these channels into a '
                   'broader omnichannel ecosystem.\n'
                   '\n'
                   'Best use / When to share:\n'
                   'Share during the Discovery or Consideration stages with digital marketing '
                   'managers, CRM leads, and e-commerce directors looking to modernize their '
                   'communication stack or combat declining email performance. It addresses pain '
                   'points around low customer visibility, slow purchasing times, and the high '
                   'costs of developing standalone brand apps by offering low-barrier, high-ROI '
                   'mobile alternatives.\n'
                   '\n'
                   'Key takeaways:\n'
                   '• Channel Breakdowns: Details the strengths of each channel, such as SMS for '
                   'offline reliability, Push for geo-targeted web/app re-engagement, Wallet for '
                   'in-store traffic and loyalty, and WhatsApp for two-way international support.\n'
                   '• Industry Use Cases: Provides tailored mobile strategies for E-commerce & '
                   'Retail, Gaming, Media & Consumer Services, Sports & Events, and Travel & '
                   'Hospitality.\n'
                   '• Success Stories: Highlights real-world impact, such as The Kooples seeing an '
                   '89% increase in sales with Wallet marketing, and the French Tennis Federation '
                   'achieving a 32% CTR via geo-fenced push notifications.\n'
                   '• Strategic Implementation: Offers a 6-step framework for combining mobile '
                   'channels with email to orchestrate holistic, automated customer journeys '
                   'without overwhelming the user.\n'
                   '\n'
                   'Search keywords:\n'
                   'mobile marketing, SMS marketing, push notifications, digital wallet, WhatsApp '
                   'business, omnichannel strategy, e-commerce, retail, gaming, travel and '
                   'hospitality, customer engagement, mobile strategy, customer retention, '
                   'WonderPush, Captain Wallet, The Kooples',
        'pain_points': '',
        'brevo_features_tags': [   'SMS Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet',
                                   'WhatsApp Marketing',
                                   'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'mobile-marketing-a-catalyst-for-growth-ebook-fr',
        'company': 'Mobile Marketing: A Catalyst for Growth',
        'title': 'Mobile Marketing: A Catalyst for Growth',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-mobile-marketing-fr-sls',
        'key_metrics': "96.5% of internet users go online via their phone — Brevo's mobile "
                       'marketing guide breaks down how SMS, push, wallet passes, and WhatsApp '
                       'each drive reach, engagement, and conversions across e-commerce, gaming, '
                       'and media.',
        'context': 'Master summary:\n'
                   'The "Mobile Marketing: A Catalyst for Growth" ebook provides a comprehensive '
                   'guide to expanding brand reach and driving engagement across mobile channels. '
                   'It breaks down the unique advantages, statistics, and industry-specific use '
                   'cases for SMS, Push Notifications, Digital Wallet, and WhatsApp marketing, '
                   'culminating in actionable strategies to integrate these channels into a '
                   'broader omnichannel ecosystem.\n'
                   '\n'
                   'Best use / When to share:\n'
                   'Share during the Discovery or Consideration stages with digital marketing '
                   'managers, CRM leads, and e-commerce directors looking to modernize their '
                   'communication stack or combat declining email performance. It addresses pain '
                   'points around low customer visibility, slow purchasing times, and the high '
                   'costs of developing standalone brand apps by offering low-barrier, high-ROI '
                   'mobile alternatives.\n'
                   '\n'
                   'Key takeaways:\n'
                   '• Channel Breakdowns: Details the strengths of each channel, such as SMS for '
                   'offline reliability, Push for geo-targeted web/app re-engagement, Wallet for '
                   'in-store traffic and loyalty, and WhatsApp for two-way international support.\n'
                   '• Industry Use Cases: Provides tailored mobile strategies for E-commerce & '
                   'Retail, Gaming, Media & Consumer Services, Sports & Events, and Travel & '
                   'Hospitality.\n'
                   '• Success Stories: Highlights real-world impact, such as The Kooples seeing an '
                   '89% increase in sales with Wallet marketing, and the French Tennis Federation '
                   'achieving a 32% CTR via geo-fenced push notifications.\n'
                   '• Strategic Implementation: Offers a 6-step framework for combining mobile '
                   'channels with email to orchestrate holistic, automated customer journeys '
                   'without overwhelming the user.\n'
                   '\n'
                   'Search keywords:\n'
                   'mobile marketing, SMS marketing, push notifications, digital wallet, WhatsApp '
                   'business, omnichannel strategy, e-commerce, retail, gaming, travel and '
                   'hospitality, customer engagement, mobile strategy, customer retention, '
                   'WonderPush, Captain Wallet, The Kooples',
        'pain_points': '',
        'brevo_features_tags': [   'SMS Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet',
                                   'WhatsApp Marketing',
                                   'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'mobile-wallet-ebook-ebook-fr',
        'company': 'Mobile Wallet Ebook',
        'title': 'Mobile Wallet Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-guide-wallet-mobile-fr-sls',
        'key_metrics': 'App retention craters from 25% to just 5% of users by day 90, and 90% of '
                       "people only ever open 5-7 apps regularly. Brevo's Mobile Wallet guide "
                       'shows how brands like Carrefour bypass the app-install problem entirely '
                       'with wallet passes that live on a screen unlocked 220 times a day.',
        'context': 'Through case studies and key figures, discover how the mobile wallet can '
                   'multiply your sales.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Customer Loyalty', 'NFC', 'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'mobile-wallet-ebook-ebook-de',
        'company': 'Mobile Wallet Ebook',
        'title': 'Mobile Wallet Ebook',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-mobile-wallet-guide-2024-sls',
        'key_metrics': 'App retention craters from 25% to just 5% of users by day 90, and 90% of '
                       "people only ever open 5-7 apps regularly. Brevo's Mobile Wallet guide "
                       'shows how brands like Carrefour bypass the app-install problem entirely '
                       'with wallet passes that live on a screen unlocked 220 times a day.',
        'context': 'Through case studies and key figures, discover how the mobile wallet can '
                   'multiply your sales.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Customer Loyalty', 'NFC', 'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'mobile-wallets-in-marketing-the-key-to-success-in-2025-dach-',
        'company': 'Mobile Wallets in Marketing: The Key to Success in 2025 (DACH)',
        'title': 'Mobile Wallets in Marketing: The Key to Success in 2025 (DACH)',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-mobile-wallets-marketing-2025-internal',
        'key_metrics': "Brevo's 2025 guide argues personalization is now the single biggest lever "
                       'for customer loyalty, and shows how mobile wallets turn that '
                       'personalization into a physical touchpoint customers carry with them, '
                       'strengthening customer experience and retention.',
        'context': 'This e-book is based on key marketing trends from the DACH region and offers '
                   'insights that remain relevant throughout the entire year. It explores how '
                   'Mobile Wallets can help businesses address essential topics such as '
                   'personalization, customer experience, sustainability, and gamification. With '
                   'practical examples and actionable strategies, the e-book demonstrates how to '
                   'build stronger customer relationships, enhance communication, and stay ahead '
                   'in 2025.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Personalization',
                                   'Customer Experience',
                                   'Customer Loyalty'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'mon-petit-prono-success-story-fr',
        'company': 'Mon Petit Prono',
        'title': 'Mon Petit Prono',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'entertainment',
        'url': 'https://www.brevo.com/fr/resources/mpp-success-story/',
        'key_metrics': 'This French football fantasy app held a 45%+ open rate on its DAILY '
                       'newsletter to 2M+ active subscribers during the 2026 World Cup (3.7M total '
                       'players) -- with just a 0.10% unsubscribe rate, thanks to lifecycle '
                       'segmentation by league/language and event-triggered automation.',
        'context': '1. Master Summary\n'
                   'Mon Petit Prono (MPP), the fantasy football prediction app created by the Mon '
                   'Petit Gazon (MPG) team and owned by LFP Media since 2022, relies on Brevo to '
                   'orchestrate its lifecycle marketing at massive scale. During the 2026 World '
                   "Cup, MPP hit a historic record of 3.7 million players, and used Brevo's "
                   'segmentation and marketing automation to keep its trademark casual, humorous '
                   'editorial tone intact while sending millions of emails without sacrificing '
                   'deliverability or engagement.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — a strong reference for brands with a strong '
                   'editorial voice and seasonal, high-intensity engagement spikes (major sporting '
                   'or entertainment events).\n'
                   'Ideal prospect profile: Consumer app or media brand with a distinctive, '
                   'community-driven editorial tone, facing sudden and massive audience growth '
                   'during specific events (sports competitions, seasonal peaks), needing to '
                   'automate lifecycle communication across email, push, in-app, and social '
                   'without becoming generic or redundant.\n'
                   'Pitch: "If your brand voice is central to your success and you\'re worried '
                   'that scaling communication to millions of users means losing that tone — Mon '
                   'Petit Prono proves otherwise. During the 2026 World Cup they sent a daily '
                   'newsletter to 2M+ active subscribers with Brevo, keeping their signature humor '
                   'intact, and still hit a 45%+ open rate with a 0.10% unsubscribe rate."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Advanced segmentation by league/competition followed and by language, '
                   'enabling highly relevant messaging at scale.\n'
                   '- Full lifecycle marketing automation triggered at key game moments (account '
                   'creation, transfer window, first team selection, weekend results, player '
                   'injuries), always avoiding generic templated copy.\n'
                   '- Daily newsletter as a retention ritual: "La Gazette MPP" sent every day '
                   'during the 2026 World Cup to 2M+ active subscribers.\n'
                   '- Deliverability at scale was a critical requirement given the exponential '
                   'audience growth during major competitions.\n'
                   '- Omnichannel consistency: email, push notifications, in-app alerts, and '
                   'social media coordinated to keep users engaged all season without being '
                   'redundant.\n'
                   '- Community proximity maintained despite scale: 500-1,000 email replies per '
                   'week, each answered individually by the MPP team, reinforcing brand advocacy.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 3.7 million users on Mon Petit Prono during the 2026 World Cup\n'
                   '- 45%+ average open rate on the daily MPP newsletter (2026 World Cup), sent to '
                   '2M+ active subscribers\n'
                   '- 0.10% unsubscribe rate despite daily sending throughout the World Cup\n'
                   '- 500-1,000 email replies received per week, all answered individually by the '
                   'MPP team\n'
                   '\n'
                   '5. Search Keywords\n'
                   'fantasy sport, sports app, football prediction, gaming entertainment, sports '
                   'entertainment, lifecycle marketing, marketing automation, segmentation, daily '
                   'newsletter, brand voice, editorial tone, deliverability at scale, omnichannel, '
                   'retention, World Cup, seasonal spike, community engagement, brand advocacy, '
                   'LFP Media, Mon Petit Gazon, Brevo Automation, Brevo Email marketing, open rate '
                   'benchmark, unsubscribe rate',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation (lifecycle triggers)',
                                   'Advanced Segmentation',
                                   'High-Frequency Newsletter Deliverability',
                                   'Omnichannel (push, in-app, social)'],
        'best_for_verticals': ['entertainment', 'sports'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'monisnap-uses-marketing-automation-to-increase-customer-loya',
        'company': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                   'Triple Money Transfer Transactions',
        'title': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                 'Triple Money Transfer Transactions',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'fintech',
        'url': 'https://www.brevo.com/success-stories/monisnap/',
        'key_metrics': 'This European money-transfer fintech tripled money-transfer transactions '
                       "and boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                       'automated marketing scenarios across email, SMS, and push.',
        'context': 'This European money-transfer fintech tripled money-transfer transactions and '
                   "boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                   'automated marketing scenarios across email, SMS, and push.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Multichannel Messaging (Email/SMS/Push)',
                                   'Customer Retention Workflows'],
        'best_for_verticals': ['fintech'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'monisnap-uses-marketing-automation-to-increase-customer-loya-2',
        'company': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                   'Triple Money Transfer Transactions',
        'title': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                 'Triple Money Transfer Transactions',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'fintech',
        'url': 'https://www.brevo.com/fr/success-stories/monisnap/',
        'key_metrics': 'This European money-transfer fintech tripled money-transfer transactions '
                       "and boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                       'automated marketing scenarios across email, SMS, and push.',
        'context': 'This European money-transfer fintech tripled money-transfer transactions and '
                   "boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                   'automated marketing scenarios across email, SMS, and push.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Multichannel Messaging (Email/SMS/Push)',
                                   'Customer Retention Workflows'],
        'best_for_verticals': ['fintech'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'monisnap-uses-marketing-automation-to-increase-customer-loya-3',
        'company': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                   'Triple Money Transfer Transactions',
        'title': 'Monisnap Uses Marketing Automation to Increase Customer Loyalty by 40% and '
                 'Triple Money Transfer Transactions',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'fintech',
        'url': 'https://www.brevo.com/de/success-stories/monisnap/',
        'key_metrics': 'This European money-transfer fintech tripled money-transfer transactions '
                       "and boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                       'automated marketing scenarios across email, SMS, and push.',
        'context': 'This European money-transfer fintech tripled money-transfer transactions and '
                   "boosted customer retention by 40% using Brevo's lead scoring plus 20+ "
                   'automated marketing scenarios across email, SMS, and push.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Lead Scoring',
                                   'Multichannel Messaging (Email/SMS/Push)',
                                   'Customer Retention Workflows'],
        'best_for_verticals': ['fintech'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'moustache-bikes-success-story-fr',
        'company': 'Moustache Bikes',
        'title': 'Moustache Bikes',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://www.brevo.com/fr/resources/moustache-bikes-success-story/',
        'key_metrics': 'This premium French e-bike brand (sold exclusively through a dealer '
                       'network) built a connected customer experience across 100,000+ contacts '
                       'and 18 automated workflows -- hitting a 44% email open rate while driving '
                       'qualified foot traffic to its retail partners.',
        'context': '1. Master Summary\n'
                   'Moustache Bikes, a French premium e-bike manufacturer (Vosges) distributing '
                   'exclusively through a network of 500+ physical dealers worldwide, uses Brevo '
                   'to build direct, automated relationships with 100,000+ end-users — despite '
                   'having no direct sales channel. By connecting its e-commerce data and CRM to '
                   "Brevo's Marketing Automation and Email platform, Moustache Bikes bridges the "
                   'gap between digital journeys and an indirect dealer network, delivering '
                   'personalized lifecycle communications to riders at scale.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — ideal for manufacturers or brands with indirect '
                   'distribution (dealers, resellers, franchisees) looking to build direct '
                   'customer relationships without bypassing their channel.\n'
                   'Ideal prospect profile: Premium B2C manufacturer or brand selling through '
                   'resellers/dealers, with a large end-user base but no direct e-commerce '
                   'relationship. Sectors: bikes, outdoor equipment, automotive, premium consumer '
                   'goods, manufacturing.\n'
                   'Pitch: "If you sell through dealers and feel like you have no visibility or '
                   'relationship with your end customers — Moustache Bikes solved exactly that. '
                   'They use Brevo to automate direct communications with 100K+ riders, even '
                   'though 100% of their sales go through a dealer network."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Indirect channel + direct CRM: proof that a manufacturer can build a direct '
                   'customer relationship even with 100% dealer-based distribution.\n'
                   '- 100K+ end-users engaged via automated journeys: onboarding, product tips, '
                   'maintenance reminders, community engagement.\n'
                   '- Marketing Automation as the bridge: connects product registration, '
                   'e-commerce data, and CRM to lifecycle email sequences.\n'
                   "- Premium brand experience at scale: personalization aligned with Moustache's "
                   'high-end brand positioning.\n'
                   "- Relevant for manufacturing and retail prospects: demonstrates Brevo's "
                   'versatility beyond pure e-commerce.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 100,000+ end-users in CRM\n'
                   '- Distribution network: 500+ dealers worldwide (45% export)\n'
                   'No email performance or revenue metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'manufacturer, indirect channel, dealer network, e-bike, premium bikes, CRM, '
                   'email marketing, marketing automation, lifecycle marketing, direct '
                   'relationship, B2C, retail, outdoor, Vosges, France, 100K users, product '
                   'registration, onboarding, community, Brevo CRM, Brevo Automation, réseau '
                   'revendeurs, relation client directe, fabricant, vélo électrique, parcours '
                   'automatisés, Facihändlernetz, Direktmarketing, Hersteller CRM, E-Bike',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation (18 workflows)',
                                   'CRM/Contact Management',
                                   'Retail/Dealer Network Enablement'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'oliviers-co-case-study-fr',
        'company': 'Oliviers & Co',
        'title': 'Oliviers & Co',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/oliviers-co-case-study-fr-sls',
        'key_metrics': 'Gourmet retailer Oliviers & Co unified scattered in-store and online data '
                       'into one Brevo CDP, using RFM scoring to win back dormant customers and '
                       'trigger automated repurchase campaigns, like a reminder sent 4 months '
                       'after an olive oil purchase.',
        'context': 'To overcome fragmented data across its global stores and e-commerce, premium '
                   'food brand Oliviers&Co deployed Brevo’s CDP to unify and score their customer '
                   'base. By leveraging this clean data for automated, targeted CRM scenarios '
                   '(like RFM-based repurchase), they successfully increased their reachable '
                   'contacts by 40% and drove a 14% growth in web revenue.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP',
                                   'Customer Data Platform',
                                   'Segmentation',
                                   'Marketing Automation',
                                   'Retail'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'omnichannel-success-with-mobile-wallets-ebook-de',
        'company': 'Omnichannel success with mobile wallets',
        'title': 'Omnichannel success with mobile wallets',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-omnichannel-erfolg-mobile-wallet-2024-sls',
        'key_metrics': '80% of shoppers research online before ever stepping into a store, per '
                       "Google — Brevo's omnichannel guide shows how mobile wallet passes bridge "
                       'that online-to-offline gap to boost loyalty and retention across every '
                       'touchpoint.',
        'context': 'This is an ebook highlighting how mobile wallet marketing can be integrated '
                   'into omnichannel marketing strategies.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Omnichannel Marketing',
                                   'Customer Experience',
                                   'Customer Loyalty'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'fintech',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'adbloom-case-study-case-study-en',
        'company': 'AdBloom Case Study',
        'title': 'One Pager: AdBloom Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'agency',
        'url': 'https://content.brevo.com/EN-AdBloom-Case-Study-sls',
        'key_metrics': 'Growth marketing agency AdBloom built a $1 million/year revenue center by '
                       'consolidating transactional email, marketing automation, segmentation, and '
                       "landing pages into Brevo's all-in-one platform, replacing costly, "
                       'disconnected point tools.',
        'context': 'This one-pager highlights how AdBloom successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Transactional Email',
                                   'Marketing Automation',
                                   'Segmentation',
                                   'Landing Pages',
                                   'Agency'],
        'best_for_verticals': ['agency'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator', 'Email Specialist', 'Saver']},
    {   'id': 'ai-camp-case-study-case-study-en',
        'company': 'AI Camp Case Study',
        'title': 'One Pager: AI Camp Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/EN-AI-Camp-Case-Study-sls',
        'key_metrics': "AI Camp saved $30k a year by switching from HubSpot to Brevo's CRM suite, "
                       'now running 200-300k emails a month plus sales pipeline management, '
                       'meeting scheduling, and Zapier-connected payment tracking in one platform.',
        'context': 'This one-pager highlights how AI Camp successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Sales CRM',
                                   'Marketing Automation',
                                   'Meetings',
                                   'Zapier Integration',
                                   'Email Marketing'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Saver']},
    {   'id': 'aquarelle-case-study-en',
        'company': 'Aquarelle',
        'title': 'One Pager: Aquarelle - Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/Aquarelle-SS-Int',
        'key_metrics': 'Flower delivery leader Aquarelle used Brevo SMS to reactivate inactive '
                       'customers, generating 10x more conversions, part of a multichannel '
                       'strategy spanning segmentation, automation, WhatsApp, push notifications, '
                       'and mobile wallet across its 3-million-contact database.',
        'context': 'This one-pager highlights how Aquarelle successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'SMS Marketing',
                                   'Segmentation',
                                   'Marketing Automation',
                                   'WhatsApp Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Network', 'Consolidator', 'Feature Specialist']},
    {   'id': 'aquarelle-case-study-fr',
        'company': 'Aquarelle',
        'title': 'One Pager: Aquarelle - Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/FR-Aquarelle-Case-Study',
        'key_metrics': 'Flower delivery leader Aquarelle used Brevo SMS to reactivate inactive '
                       'customers, generating 10x more conversions, part of a multichannel '
                       'strategy spanning segmentation, automation, WhatsApp, push notifications, '
                       'and mobile wallet across its 3-million-contact database.',
        'context': 'This one-pager highlights how Aquarelle successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'SMS Marketing',
                                   'Segmentation',
                                   'Marketing Automation',
                                   'WhatsApp Marketing',
                                   'Push Notifications',
                                   'Mobile Wallet'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Network', 'Consolidator', 'Feature Specialist']},
    {   'id': 'burda-style-case-study-case-study-en',
        'company': 'Burda Style Case Study',
        'title': 'One Pager: Burda Style Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/EN-Burda-Success-Story-sls',
        'key_metrics': 'Burda Style, published in 17 languages across 100+ countries, streamlined '
                       "marketing for all its regional sites using Brevo's multi-account solution, "
                       'giving each website its own sub-account with tailored automation, '
                       'personalization, and lead scoring.',
        'context': 'This one-pager highlights how Burda successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Multi-Account Management',
                                   'Marketing Automation',
                                   'Personalization',
                                   'Lead Scoring',
                                   'Email Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'burda-style-case-study-case-study-de',
        'company': 'Burda Style Case Study',
        'title': 'One Pager: Burda Style Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/DE-Burda-Success-Story',
        'key_metrics': 'Burda Style, published in 17 languages across 100+ countries, streamlined '
                       "marketing for all its regional sites using Brevo's multi-account solution, "
                       'giving each website its own sub-account with tailored automation, '
                       'personalization, and lead scoring.',
        'context': 'This one-pager highlights how Burda successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Multi-Account Management',
                                   'Marketing Automation',
                                   'Personalization',
                                   'Lead Scoring',
                                   'Email Marketing'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Network']},
    {   'id': 'florida-trend-case-study-case-study-en',
        'company': 'Florida Trend Case Study',
        'title': 'One Pager: Florida Trend Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/EN-Florida-Trend-Case-Study-sls',
        'key_metrics': "Florida Trend, the US's first regional business magazine, hit 50% open "
                       "rates on some newsletters by using Brevo's dynamic contact segmentation to "
                       'reliably send over 2 million emails a month.',
        'context': 'This one-pager highlights how Florida Trend successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Platform',
                                   'Dynamic Contact Segmentation',
                                   'Email Deliverability',
                                   'Customer Success Manager',
                                   'Campaign Reporting'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'great-british-chefs-case-study-en',
        'company': 'Great British Chefs',
        'title': 'One Pager: Great British Chefs - Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/GBC-SS-Ent',
        'key_metrics': "Great British Chefs boosted email open rates by 10% by combining Brevo's "
                       'dynamic segmentation, automation, and Shopify integration to engage the '
                       "UK's 13 million foodies.",
        'context': 'This one-pager highlights how Great British Chefs successfully leveraged Brevo '
                   'to overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Email API',
                                   'Dynamic Segmentation',
                                   'Shopify Integration',
                                   'Customer Success Manager'],
        'best_for_verticals': ['retail', 'media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'heylo-case-study-case-study-en',
        'company': 'Heylo Case Study',
        'title': 'One Pager: Heylo Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/EN-Heylo-Case-Study-sls',
        'key_metrics': 'Heylo scaled its email volume from a few hundred sends a month to nearly 1 '
                       "million using Brevo's Email API and automation — growing 20% together with "
                       'Brevo.',
        'context': 'This one-pager highlights how Heylo successfully leveraged Brevo to overcome '
                   'key challenges and achieve their business goals. It showcases the solutions '
                   'implemented and the measurable impact, offering a real-world example of '
                   "Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': ['Email API', 'Marketing Platform', 'Marketing Automation'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Email Specialist']},
    {   'id': 'hi-rez-studios-case-study-case-study-en',
        'company': 'Hi-Rez Studios Case Study',
        'title': 'One Pager: Hi-Rez Studios Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/EN-HiRez-Studios-Case-Study-sls',
        'key_metrics': 'Hi-Rez Studios saw a 210% jump in new players from its second '
                       'refer-a-friend campaign versus the first, while boosting overall player '
                       'engagement 10% through personalized segmentation.',
        'context': 'This one-pager highlights how Hi-Rez Studios successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Email API',
                                   'Audience Segmentation',
                                   'Customer Success Manager',
                                   'Campaign Reporting'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'island-federal-case-study-case-study-en',
        'company': 'Island Federal Case Study',
        'title': 'One Pager: Island Federal Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'fintech',
        'url': 'https://content.brevo.com/EN-Island-Federal-Case-Study-sls',
        'key_metrics': 'Island Federal Credit Union hit 80% email open rates and near-zero '
                       "unsubscribes by replacing a spam-flagged provider with Brevo's automation, "
                       'segmentation, and predictive sending AI.',
        'context': 'This one-pager highlights how Island Federal successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Predictive Sending AI',
                                   'Audience Segmentation',
                                   'Email Deliverability'],
        'best_for_verticals': ['fintech'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist']},
    {   'id': 'recording-studio-london-case-study-en',
        'company': 'Recording Studio London',
        'title': 'One Pager: Recording Studio London - Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/Recording-SS-Int',
        'key_metrics': 'The Recording Studio London erased its marketing-and-sales data silos by '
                       'centralizing phone, WhatsApp, email, and web leads into one Brevo pipeline '
                       '— as their director called it, incredible value for a true all-in-one '
                       'suite.',
        'context': 'This one-pager highlights how Recording Studio London successfully leveraged '
                   'Brevo to overcome key challenges and achieve their business goals. It '
                   'showcases the solutions implemented and the measurable impact, offering a '
                   "real-world example of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Sales Platform (CRM)',
                                   'Marketing Platform',
                                   'Conversations Platform (Omnichannel)',
                                   'Automation'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'solidarites-international-case-study-en',
        'company': 'Solidarites International',
        'title': 'One Pager: Solidarites International - Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'nonprofit',
        'url': 'https://content.brevo.com/EN-SolidaritesInternational-CaseStudy-sls',
        'key_metrics': 'Solidarites International doubled its fundraising email open rates after '
                       "moving off a costly, unintuitive provider to Brevo's user-friendly "
                       'platform.',
        'context': 'This one-pager highlights how Solidarites International successfully leveraged '
                   'Brevo to overcome key challenges and achieve their business goals. It '
                   'showcases the solutions implemented and the measurable impact, offering a '
                   "real-world example of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Platform',
                                   'Customer Success Manager',
                                   'Drag-and-Drop Email Editor',
                                   'Campaign Performance Reporting'],
        'best_for_verticals': ['nonprofit'],
        'best_for_signals': [],
        'archetype_fit': ['Saver']},
    {   'id': 'solidarites-international-case-study-fr',
        'company': 'Solidarites International',
        'title': 'One Pager: Solidarites International - Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'nonprofit',
        'url': 'https://content.brevo.com/FR-SolidaritesInternational-Case-Study',
        'key_metrics': 'Solidarites International doubled its fundraising email open rates after '
                       "moving off a costly, unintuitive provider to Brevo's user-friendly "
                       'platform.',
        'context': 'This one-pager highlights how Solidarites International successfully leveraged '
                   'Brevo to overcome key challenges and achieve their business goals. It '
                   'showcases the solutions implemented and the measurable impact, offering a '
                   "real-world example of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing Platform',
                                   'Customer Success Manager',
                                   'Drag-and-Drop Email Editor',
                                   'Campaign Performance Reporting'],
        'best_for_verticals': ['nonprofit'],
        'best_for_signals': [],
        'archetype_fit': ['Saver']},
    {   'id': 'trusted-shops-case-study-en',
        'company': 'Trusted Shops',
        'title': 'One Pager: Trusted Shops - Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/Trusted-Shops-SS-Int',
        'key_metrics': 'Trusted Shops reactivated 21% of its unengaged contacts — including 10,000 '
                       'dormant subscribers — and lifted open rates to 30% (36% on specialized '
                       "sends) using Brevo's GDPR-compliant marketing automation.",
        'context': 'This one-pager highlights how Trusted Shops successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Segmentation & Dynamic Content',
                                   'GDPR Compliance',
                                   'Email Marketing Platform'],
        'best_for_verticals': ['tech_saas', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'trusted-shops-case-study-de',
        'company': 'Trusted Shops',
        'title': 'One Pager: Trusted Shops - Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/DE-TrustedShops-Case-Study',
        'key_metrics': 'Trusted Shops reactivated 21% of its unengaged contacts — including 10,000 '
                       'dormant subscribers — and lifted open rates to 30% (36% on specialized '
                       "sends) using Brevo's GDPR-compliant marketing automation.",
        'context': 'This one-pager highlights how Trusted Shops successfully leveraged Brevo to '
                   'overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Segmentation & Dynamic Content',
                                   'GDPR Compliance',
                                   'Email Marketing Platform'],
        'best_for_verticals': ['tech_saas', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'zinatt-technologies-case-study-case-study-en',
        'company': 'Zinatt Technologies Case Study',
        'title': 'One Pager: Zinatt Technologies Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'tech_saas',
        'url': 'https://content.brevo.com/EN-Zinatt-Technologies-Case-Study-sls',
        'key_metrics': 'Zinatt Technologies replaced two disconnected marketing/CRM tools with one '
                       'Brevo suite to track every prospect from first touch to closing — "Brevo '
                       'is one-stop," says their Director of Business Development.',
        'context': 'This one-pager highlights how Zinatt Technologies successfully leveraged Brevo '
                   'to overcome key challenges and achieve their business goals. It showcases the '
                   'solutions implemented and the measurable impact, offering a real-world example '
                   "of Brevo's value in action.",
        'pain_points': '',
        'brevo_features_tags': [   'Sales Platform (CRM)',
                                   'Marketing Platform',
                                   'Segmentation',
                                   'Deal Pipeline Tracking'],
        'best_for_verticals': ['tech_saas'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'origine-cycles-success-story-fr',
        'company': 'Origine Cycles',
        'title': 'Origine Cycles',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://www.brevo.com/fr/resources/origine-cycles-success-story/',
        'key_metrics': 'This French custom-bike D2C manufacturer unified marketing, sales, and '
                       'after-sales support on Brevo -- sending 500K emails/month alongside a '
                       '19-seat Sales Platform (Conversations + Phone) to stop teams bouncing '
                       'between tools.',
        'context': '1. Master Summary\n'
                   'Origine Cycles, French manufacturer of fully customizable premium bikes sold '
                   "exclusively D2C, deployed Brevo's Enterprise platform to unify its Marketing, "
                   'Sales, and Customer Support teams on a single tool. With 19 users on the Sales '
                   'Platform (Conversations + Phone), 500K emails/month managed by marketing, and '
                   'all teams operating from shared data, Brevo replaced a fragmented multi-tool '
                   'setup with one centralized, intuitive platform. The decision came down to '
                   'three criteria: Made in France, unified interface, and fair pricing.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — especially when a prospect is juggling separate '
                   'tools for sales, marketing, and support and losing time to context-switching.\n'
                   'Ideal prospect profile: Mid-market D2C or e-commerce brand with a growing team '
                   '(10-50 users), where Sales, Marketing, and Support need to share a single '
                   'customer view. Relevant sectors: retail, manufacturing, premium consumer '
                   'goods.\n'
                   'Pitch: "If your sales and support teams are on different tools from your '
                   "marketing team and everyone's losing time switching between them — Origine "
                   'Cycles solved exactly that. They now have 19 users on Brevo Sales Platform '
                   'handling conversations and calls, while marketing sends 500K emails a month '
                   'from the same platform."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Full team unification: Marketing (campaigns + CRM), Sales (Conversations + '
                   'Phone), and Support all on one platform — no more context-switching.\n'
                   '- 19 users on Sales Platform: strong adoption signal across commercial and '
                   'support teams.\n'
                   '- 500K emails/month: demonstrates volume capability alongside the Sales and '
                   'Support use case.\n'
                   '- Made in France positioning: key decision criterion for Origine Cycles, '
                   'resonates with French-market prospects sensitive to data sovereignty.\n'
                   '- Time savings as primary value: "Au quotidien, Brevo nous fait gagner un '
                   'temps précieux." (Quentin Guignard, Directeur Marketing et Communication)\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 19 users on Sales Platform (Conversations + Phone)\n'
                   '- 500,000 emails sent per month\n'
                   '- Products used: Marketing Platform Enterprise, Sales Platform, Conversations, '
                   'Phone\n'
                   'No revenue or conversion metrics published in this asset.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'Sales Platform, Conversations, Phone, email marketing, D2C, '
                   'direct-to-consumer, premium retail, manufacturing, bikes, team unification, '
                   'all-in-one, Made in France, data sovereignty, CRM, marketing automation, 500K '
                   'emails, support, mid-market, Brevo Enterprise, interface unifiée, gain de '
                   'temps, équipe commerciale, SAV, vente directe, vélos haut de gamme, '
                   'Verkaufsplattform, Kundenkommunikation, All-in-one CRM, Datenhoheit',
        'pain_points': '',
        'brevo_features_tags': [   'Sales Platform (Conversations, Phone/Telephony)',
                                   'High-Volume Email Marketing',
                                   'Unified Customer Data',
                                   'Marketing Platform Enterprise'],
        'best_for_verticals': ['retail'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'ouest-france-onepager-case-study-fr',
        'company': 'Ouest France Onepager',
        'title': 'Ouest France Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'media_publishing',
        'url': 'https://content.brevo.com/onepager-ouest-france-2-fr-sls',
        'key_metrics': 'Ouest France sends 700 million emails a year and 1.2 million newsletters a '
                       "day to 1 million subscribers on Brevo's Email API — proof the platform "
                       'holds up at true enterprise-publisher scale.',
        'context': 'Discover how Ouest France uses Brevo to improve the delivery of millions of '
                   'daily newsletters with the email API, in a one page.',
        'pain_points': '',
        'brevo_features_tags': [   'Email API',
                                   'Email Deliverability',
                                   'Multiple Dedicated IPs',
                                   'Audience Segmentation',
                                   'Customer Success Manager'],
        'best_for_verticals': ['media_publishing'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Consolidator', 'Email Specialist']},
    {   'id': 'paris-la-d-fense-success-story-fr',
        'company': 'Paris La Défense',
        'title': 'Paris La Défense',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'public_sector',
        'url': 'https://www.brevo.com/fr/resources/paris-la-defense-success-story/',
        'key_metrics': "Europe's largest business district (200,000 employees, 70,000 students, "
                       '50,000 residents) runs its Sales Platform to track every corporate event '
                       'and sponsorship request end-to-end -- replacing ad hoc email chains with '
                       'custom pipelines for its B2B/B2C events team.',
        'context': '1. Master Summary\n'
                   'Paris La Défense, the public body responsible for developing, managing, and '
                   "promoting Europe's leading business district, uses Brevo's Sales Platform to "
                   'structure and track its event and business animation requests. The events team '
                   'gained a real CRM/Sales tool to manage complex, multi-partner opportunities '
                   'end-to-end, while marketing teams use the same platform to centralize '
                   'omnichannel communication to a very broad B2B and B2C audience (companies, '
                   'developers, employees, students, residents).\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo — useful for objection handling on '
                   'public-sector/institutional prospects juggling both B2B and B2C communication '
                   'needs.\n'
                   'Ideal prospect profile: Public sector or institutional body (economic '
                   'development agency, territory management, chamber of commerce) managing '
                   'complex event/sponsorship requests involving multiple partners, alongside '
                   'large mixed B2B/B2C audiences.\n'
                   'Pitch: "If your events team is still tracking sponsorship or animation '
                   'requests by email with no structured pipeline or history — Paris La Défense '
                   "solved exactly that with Brevo's Sales Platform, using custom pipelines to "
                   'track every event opportunity end-to-end while marketing keeps omnichannel '
                   'communication centralized for both businesses and residents."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Sales Platform as the CRM backbone for events: custom pipelines let teams '
                   'track each commercial/event request step by step, with a clear history of '
                   'exchanges.\n'
                   '- Answers a public-sector-specific challenge: structuring '
                   'sponsorship/animation requests that involve many external partners, beyond '
                   'simple email exchanges.\n'
                   '- Dual audience, one platform: institutional communication reaches both B2B '
                   '(developers, companies) and B2C (employees, students, residents) from the same '
                   'tool.\n'
                   '- Base qualification cited as one of three pillars of the rollout, alongside '
                   'custom pipelines and omnichannel.\n'
                   '- Relevant reference for public sector / territory management prospects with '
                   'complex commercial project tracking needs.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- Scale of the territory served: 50,000 residents, 70,000 students, 200,000 '
                   'employees (context on audience size, not a performance metric).\n'
                   '- No conversion, revenue, or campaign performance figures are published in '
                   'this success story.\n'
                   '\n'
                   '5. Search Keywords\n'
                   'public sector, territory management, business district, events, Sales '
                   'Platform, CRM, custom pipelines, sponsorship, business animations, B2B B2C '
                   'communication, omnichannel, institutional communication, Paris La Défense, '
                   'complex opportunities, base qualification, segmentation, Brevo Sales Platform, '
                   'Brevo CRM, öffentlicher Sektor',
        'pain_points': '',
        'brevo_features_tags': [   'Sales Platform (custom pipelines)',
                                   'CRM for Event/Partnership Management',
                                   'Omnichannel Audience Communication'],
        'best_for_verticals': ['public_sector'],
        'best_for_signals': [],
        'archetype_fit': []},
    {   'id': 'psg-case-study-case-study-de',
        'company': 'PSG Case Study',
        'title': 'PSG Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/de-case-study-psg-push-2024-sls',
        'key_metrics': 'Paris Saint-Germain drives a 20% click-through rate on push notifications '
                       'sharing match highlights and team news — turning casual site visitors into '
                       'engaged, opted-in fans.',
        'context': 'A case study highlighting how the football club PSG wins and retains customers '
                   'thanks to push-notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications (Web & Mobile)',
                                   'Real-Time Alerts',
                                   'Audience Segmentation'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-case-study-case-study-fr',
        'company': 'PSG Case Study',
        'title': 'PSG Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/usecase-psg-fr-sls',
        'key_metrics': 'Paris Saint-Germain drives a 20% click-through rate on push notifications '
                       'sharing match highlights and team news — turning casual site visitors into '
                       'engaged, opted-in fans.',
        'context': 'A case study highlighting how the football club PSG wins and retains customers '
                   'thanks to push-notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications (Web & Mobile)',
                                   'Real-Time Alerts',
                                   'Audience Segmentation'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-case-study-case-study-en',
        'company': 'PSG Case Study',
        'title': 'PSG Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'entertainment',
        'url': 'https://content.brevo.com/usecase-psg-eng-sls',
        'key_metrics': 'Paris Saint-Germain drives a 20% click-through rate on push notifications '
                       'sharing match highlights and team news — turning casual site visitors into '
                       'engaged, opted-in fans.',
        'context': 'A case study highlighting how the football club PSG wins and retains customers '
                   'thanks to push-notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications (Web & Mobile)',
                                   'Real-Time Alerts',
                                   'Audience Segmentation'],
        'best_for_verticals': ['entertainment'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-onepager-case-study-fr',
        'company': 'PSG Onepager',
        'title': 'PSG Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'sports',
        'url': 'https://content.brevo.com/onepager-psg-fr-sls',
        'key_metrics': "PSG's push notification program with Brevo delivers a 20% average "
                       'click-through rate, with 80% of subscribers clicking at least once on a '
                       'campaign and 50% returning to the app thanks to real-time alerts.',
        'context': 'Discover how PSG uses Brevo to recruit and engage subscribers with push '
                   'notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Real-Time Alerts',
                                   'Mobile & Web Push',
                                   'Multilingual Campaign Automation'],
        'best_for_verticals': ['sports'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-onepager-case-study-en',
        'company': 'PSG Onepager',
        'title': 'PSG Onepager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'sports',
        'url': 'https://content.brevo.com/onepager-psg-en-sls',
        'key_metrics': "PSG's push notification program with Brevo delivers a 20% average "
                       'click-through rate, with 80% of subscribers clicking at least once on a '
                       'campaign and 50% returning to the app thanks to real-time alerts.',
        'context': 'Discover how PSG uses Brevo to recruit and engage subscribers with push '
                   'notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Real-Time Alerts',
                                   'Mobile & Web Push',
                                   'Multilingual Campaign Automation'],
        'best_for_verticals': ['sports'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-onepager-case-study-es',
        'company': 'PSG Onepager',
        'title': 'PSG Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'sports',
        'url': 'https://content.brevo.com/onepager-psg-es-sls',
        'key_metrics': "PSG's push notification program with Brevo delivers a 20% average "
                       'click-through rate, with 80% of subscribers clicking at least once on a '
                       'campaign and 50% returning to the app thanks to real-time alerts.',
        'context': 'Discover how PSG uses Brevo to recruit and engage subscribers with push '
                   'notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Real-Time Alerts',
                                   'Mobile & Web Push',
                                   'Multilingual Campaign Automation'],
        'best_for_verticals': ['sports'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'psg-onepager-case-study-de',
        'company': 'PSG Onepager',
        'title': 'PSG Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'sports',
        'url': 'https://content.brevo.com/onepager-psg-de-sls',
        'key_metrics': "PSG's push notification program with Brevo delivers a 20% average "
                       'click-through rate, with 80% of subscribers clicking at least once on a '
                       'campaign and 50% returning to the app thanks to real-time alerts.',
        'context': 'Discover how PSG uses Brevo to recruit and engage subscribers with push '
                   'notifications.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Real-Time Alerts',
                                   'Mobile & Web Push',
                                   'Multilingual Campaign Automation'],
        'best_for_verticals': ['sports'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist', 'Feature Specialist']},
    {   'id': 'push-notification-wallet-mobile-ebook-ebook-fr',
        'company': 'Push Notification & Wallet Mobile Ebook',
        'title': 'Push Notification & Wallet Mobile Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-push-notifications-wallet-mobile-fr-sls',
        'key_metrics': "This ebook shows how Maison 123's mobile wallet loyalty card doubled "
                       'customer revenue and lifted purchase frequency 71% versus non-wallet '
                       'customers, for an estimated 36.5x ROI.',
        'context': 'Push notifications and the mobile wallet create a powerful synergy that '
                   'dramatically boosts customer engagement and marketing performance. The winning '
                   'combo for engaging and retaining your customers.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Push Notifications', 'Loyalty Programs'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'ratp-dev-success-story-fr',
        'company': 'RATP Dev',
        'title': 'RATP Dev',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'transportation',
        'url': 'https://www.brevo.com/fr/resources/ratp-dev-success-story/',
        'key_metrics': 'This RATP Group transit operator (16 countries, dozens of subsidiary '
                       'networks) runs a master account + sub-account model across 140 users and 7 '
                       'dedicated IPs -- hitting a 27% open rate (vs. 20-22% industry average) and '
                       '93% deliverability on both email and SMS for millions of riders.',
        'context': '1. Master Summary\n'
                   'RATP Dev, a subsidiary of Groupe RATP operating multimodal transport networks '
                   '(bus, tram, metro, train) in 16 countries across 5 continents, has used Brevo '
                   'since May 2023 to unify communication across dozens of subsidiaries while '
                   "preserving each network's autonomy. Through a reseller multi-sub-account model "
                   '— 1 master account with 7 dedicated IPs and several dozen autonomous '
                   'sub-accounts — RATP Dev centralizes performance oversight and deliverability '
                   'quality while letting each subsidiary manage its own campaigns, lists, and '
                   'automations across the full passenger communication cycle.\n'
                   '\n'
                   '2. When to Use This\n'
                   'Sales stage: Discovery, Demo, Proposal — strong reference for objection '
                   'handling on multi-entity governance, deliverability at scale, and IP '
                   'reputation management.\n'
                   'Ideal prospect profile: Large multi-subsidiary or multi-network organization '
                   '(transport, franchise, public services) needing a single platform where each '
                   'entity runs autonomous campaigns while a master account keeps centralized '
                   'oversight of performance and sending reputation. Particularly relevant for '
                   'international expansion scenarios.\n'
                   'Pitch: "If you\'re managing communications across dozens of subsidiaries or '
                   'networks and need local autonomy without losing centralized visibility on '
                   'deliverability — RATP Dev is a strong reference. They run 1 master account '
                   'with dedicated IPs and dozens of autonomous sub-accounts, covering the full '
                   'passenger journey from transactional alerts to marketing campaigns and SMS."\n'
                   '\n'
                   '3. Key Takeaways\n'
                   '- Reseller multi-sub-account architecture: 1 master account (7 dedicated IPs) '
                   'for centralized oversight, dozens of autonomous sub-accounts for local '
                   'campaign management, 140 users across all entities.\n'
                   '- Full communication cycle covered: transactional emails (real-time traffic '
                   'info, service tracking, disruption alerts), marketing campaigns (promotions, '
                   'contests, loyalty), SMS (urgent alerts, departure notifications, local '
                   'communications), automation (welcome scenarios, reminders, behavioral '
                   'notifications), and forms/landing pages for data and opt-in collection.\n'
                   '- Dedicated IP management protects sending reputation at scale across a '
                   'high-volume, multi-entity sender.\n'
                   '- Scalable model supporting international network growth, including outside '
                   'France.\n'
                   '- Strong deliverability proof point for a demanding, high-volume transactional '
                   'and marketing sender.\n'
                   '\n'
                   '4. Key KPIs, Figures & Insights\n'
                   '- 93% deliverability rate on marketing emails\n'
                   '- 27% open rate, above the transport industry average (20-22%)\n'
                   '- 93% deliverability rate on SMS\n'
                   '- 1 master account, 7 dedicated IPs, dozens of autonomous sub-accounts, 140 '
                   'users\n'
                   '- Live since May 2023\n'
                   '\n'
                   '5. Search Keywords\n'
                   'multi-account, sub-accounts, reseller model, master account, dedicated IP, '
                   'deliverability, transport, mobility, public transport, transactional email, '
                   'SMS, marketing automation, campaign management, multi-subsidiary, '
                   'multi-network, international expansion, forms, landing pages, high-volume '
                   'sender, IP reputation, Brevo Enterprise, Brevo dedicated IP, RATP Dev, '
                   'transport industry benchmark',
        'pain_points': '',
        'brevo_features_tags': [   'Multi-Account/Sub-Account Architecture',
                                   'Dedicated IP Management',
                                   'Transactional & Marketing Email',
                                   'SMS Campaigns',
                                   'Marketing Automation'],
        'best_for_verticals': ['transportation'],
        'best_for_signals': [],
        'archetype_fit': ['Network', 'Email Specialist']},
    {   'id': 'salomon-case-study-case-study-de',
        'company': 'Salomon Case Study',
        'title': 'Salomon Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-use-case-salomon-wallet-2024-sls',
        'key_metrics': "Salomon ditched costly SMS for Brevo's Mobile Wallet to reach customers "
                       'directly on their lock screens — powering automated event '
                       'reminders/cancellations and an international S/PLUS loyalty card live '
                       'across 18+ countries, with zero app download required.',
        'context': 'The Wallet, a worldwide communication channel for Salomon!\n'
                   'Salomon has been using the Mobile Wallet for several years (since 2019) for '
                   'two reasons:\n'
                   'Digitization of registrations for their own events.\n'
                   'Digitization of the S/PLUS membership card.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Push Notifications',
                                   'Event Marketing'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist', 'Saver']},
    {   'id': 'synergies-of-mobile-wallets-loyalty-programs-ebook-de',
        'company': 'Synergies of mobile wallets & loyalty programs',
        'title': 'Synergies of mobile wallets & loyalty programs',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/de-wallet-loyalty-2024-sls',
        'key_metrics': 'Retailer Botanic used in-store QR codes to push loyalty card sign-ups '
                       "straight into customers' mobile wallets, hitting a 79% install rate and a "
                       '98.8% card retention rate once added — proof wallet-based loyalty cards '
                       "simply don't get deleted like plastic ones.",
        'context': 'This is an ebook highlighting the relevance of integrating mobile wallet '
                   'marketing into a loyalty program.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'CRM'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'nonprofit',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'synergies-of-mobile-wallets-loyalty-programs-ebook-fr',
        'company': 'Synergies of mobile wallets & loyalty programs',
        'title': 'Synergies of mobile wallets & loyalty programs',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/ebook-wallet-loyalty-fr-sls',
        'key_metrics': 'Retailer Botanic used in-store QR codes to push loyalty card sign-ups '
                       "straight into customers' mobile wallets, hitting a 79% install rate and a "
                       '98.8% card retention rate once added — proof wallet-based loyalty cards '
                       "simply don't get deleted like plastic ones.",
        'context': 'This is an ebook highlighting the relevance of integrating mobile wallet '
                   'marketing into a loyalty program.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'CRM'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'nonprofit',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'synergies-of-mobile-wallets-loyalty-programs-ebook-en',
        'company': 'Synergies of mobile wallets & loyalty programs',
        'title': 'Synergies of mobile wallets & loyalty programs',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/ebook-wallet-loyalty-en-sls',
        'key_metrics': 'Retailer Botanic used in-store QR codes to push loyalty card sign-ups '
                       "straight into customers' mobile wallets, hitting a 79% install rate and a "
                       '98.8% card retention rate once added — proof wallet-based loyalty cards '
                       "simply don't get deleted like plastic ones.",
        'context': 'This is an ebook highlighting the relevance of integrating mobile wallet '
                   'marketing into a loyalty program.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'CRM'],
        'best_for_verticals': [   'ecommerce',
                                  'media_publishing',
                                  'retail',
                                  'hospitality',
                                  'public_sector',
                                  'tech_saas',
                                  'nonprofit',
                                  'entertainment'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'thalgo-success-story-fr',
        'company': 'Thalgo',
        'title': 'Thalgo',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://www.brevo.com/fr/resources/thalgo-success-story/',
        'key_metrics': 'This French marine-cosmetics group (30,000+ employees) drove +30% revenue '
                       'growth in France after deploying automation for the first time -- now '
                       'running 17 brand sub-accounts from one interface at 97% deliverability, '
                       'plus live chat and web push.',
        'context': 'Thalgo centralized its multi-brand strategy using Brevo by managing 17 '
                   'sub-accounts from a single interface, ensuring both global governance and '
                   'local autonomy. By leveraging marketing automation, pop-ups, and the '
                   'Conversations chatbot, they successfully boosted their revenue in France by '
                   '30% while maintaining excellent email deliverability.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Multi-Account Management',
                                   'Live Chat/Conversations',
                                   'Web Push Notifications'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Network', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'thalgo-success-story-en',
        'company': 'Thalgo',
        'title': 'Thalgo',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://www.brevo.com/resources/thalgo-success-story/',
        'key_metrics': 'This French marine-cosmetics group (30,000+ employees) drove +30% revenue '
                       'growth in France after deploying automation for the first time -- now '
                       'running 17 brand sub-accounts from one interface at 97% deliverability, '
                       'plus live chat and web push.',
        'context': 'Thalgo centralized its multi-brand strategy using Brevo by managing 17 '
                   'sub-accounts from a single interface, ensuring both global governance and '
                   'local autonomy. By leveraging marketing automation, pop-ups, and the '
                   'Conversations chatbot, they successfully boosted their revenue in France by '
                   '30% while maintaining excellent email deliverability.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation',
                                   'Multi-Account Management',
                                   'Live Chat/Conversations',
                                   'Web Push Notifications'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Graduate', 'Network', 'Email Specialist', 'Feature Specialist']},
    {   'id': 'the-complete-guide-to-email-marketing-for-ecommerce-ebook-en',
        'company': 'The complete guide to email marketing for ecommerce',
        'title': 'The complete guide to email marketing for ecommerce',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://corp-backend.brevo.com/wp-content/uploads/2023/06/email-marketing-for-ecommerce-EN.pdf',
        'key_metrics': 'A complete guide to ecommerce email marketing -- covering everything from '
                       'campaign foundations to conversion best practices -- built to help brands '
                       'gain loyalty and drive acquisition through personalization.',
        'context': 'A complete guide to ecommerce email marketing -- covering everything from '
                   'campaign foundations to conversion best practices -- built to help brands gain '
                   'loyalty and drive acquisition through personalization.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Customer Acquisition',
                                   'Customer Loyalty',
                                   'Ecommerce'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-complete-guide-to-email-marketing-for-ecommerce-ebook-fr',
        'company': 'The complete guide to email marketing for ecommerce',
        'title': 'The complete guide to email marketing for ecommerce',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'http://corp-backend.brevo.com/fr/wp-content/uploads/sites/4/2023/06/email-marketing-for-ecommerce-FR.pdf',
        'key_metrics': 'A complete guide to ecommerce email marketing -- covering everything from '
                       'campaign foundations to conversion best practices -- built to help brands '
                       'gain loyalty and drive acquisition through personalization.',
        'context': 'A complete guide to ecommerce email marketing -- covering everything from '
                   'campaign foundations to conversion best practices -- built to help brands gain '
                   'loyalty and drive acquisition through personalization.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Customer Acquisition',
                                   'Customer Loyalty',
                                   'Ecommerce'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-complete-guide-to-email-marketing-for-ecommerce-ebook-de',
        'company': 'The complete guide to email marketing for ecommerce',
        'title': 'The complete guide to email marketing for ecommerce',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'http://corp-backend.brevo.com/de/wp-content/uploads/sites/5/2023/06/Email-Marketing-for-Ecommerce-DE.pdf',
        'key_metrics': 'A complete guide to ecommerce email marketing -- covering everything from '
                       'campaign foundations to conversion best practices -- built to help brands '
                       'gain loyalty and drive acquisition through personalization.',
        'context': 'A complete guide to ecommerce email marketing -- covering everything from '
                   'campaign foundations to conversion best practices -- built to help brands gain '
                   'loyalty and drive acquisition through personalization.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Personalization',
                                   'Customer Acquisition',
                                   'Customer Loyalty',
                                   'Ecommerce'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': ['has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-case-study-case-study-de',
        'company': 'The Kooples Case Study',
        'title': 'The Kooples Case Study',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/success-story-the-kooples-de-2024-sls',
        'key_metrics': 'The Kooples grew revenue per customer by 89% and repeat purchases by 90% '
                       "just by moving its loyalty card into Brevo's Mobile Wallet, with 98% card "
                       'retention and walletized customers going omnichannel at 3x the rate of '
                       'non-walletized ones (52% vs 16%).',
        'context': 'Discover how The Kooples boosted customer loyalty with their wallet strategy! '
                   'In this success story, you’ll see how they drove impressive results like '
                   'increased retention and higher conversion rates. Explore examples of their top '
                   'wallet campaigns and gain actionable insights to enhance customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Push Notifications',
                                   'Omnichannel'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-case-study-case-study-fr',
        'company': 'The Kooples Case Study',
        'title': 'The Kooples Case Study',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/success-story-the-kooples-fr-2024',
        'key_metrics': 'The Kooples grew revenue per customer by 89% and repeat purchases by 90% '
                       "just by moving its loyalty card into Brevo's Mobile Wallet, with 98% card "
                       'retention and walletized customers going omnichannel at 3x the rate of '
                       'non-walletized ones (52% vs 16%).',
        'context': 'Discover how The Kooples boosted customer loyalty with their wallet strategy! '
                   'In this success story, you’ll see how they drove impressive results like '
                   'increased retention and higher conversion rates. Explore examples of their top '
                   'wallet campaigns and gain actionable insights to enhance customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Push Notifications',
                                   'Omnichannel'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-case-study-case-study-en',
        'company': 'The Kooples Case Study',
        'title': 'The Kooples Case Study',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://content.brevo.com/success-story-the-kooples-2024',
        'key_metrics': 'The Kooples grew revenue per customer by 89% and repeat purchases by 90% '
                       "just by moving its loyalty card into Brevo's Mobile Wallet, with 98% card "
                       'retention and walletized customers going omnichannel at 3x the rate of '
                       'non-walletized ones (52% vs 16%).',
        'context': 'Discover how The Kooples boosted customer loyalty with their wallet strategy! '
                   'In this success story, you’ll see how they drove impressive results like '
                   'increased retention and higher conversion rates. Explore examples of their top '
                   'wallet campaigns and gain actionable insights to enhance customer engagement.',
        'pain_points': '',
        'brevo_features_tags': [   'Mobile Wallet',
                                   'Loyalty Program',
                                   'Push Notifications',
                                   'Omnichannel'],
        'best_for_verticals': ['ecommerce', 'retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-onepager-case-study-fr',
        'company': 'The Kooples Onepager',
        'title': 'The Kooples Onepager',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-the-kooples-fr-sls',
        'key_metrics': 'How The Kooples increased revenue per customer by 89% through mobile '
                       'wallets — a one-page snapshot of the objectives, rollout, and results (90% '
                       'repeat purchase lift, 98% card retention).',
        'context': 'Discover how The Kooples uses Brevo, and more specifically the mobile wallet, '
                   'to increase its revenue per customer.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Push Notifications'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-onepager-case-study-en',
        'company': 'The Kooples Onepager',
        'title': 'The Kooples Onepager',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-the-kooples-en-sls',
        'key_metrics': 'How The Kooples increased revenue per customer by 89% through mobile '
                       'wallets — a one-page snapshot of the objectives, rollout, and results (90% '
                       'repeat purchase lift, 98% card retention).',
        'context': 'Discover how The Kooples uses Brevo, and more specifically the mobile wallet, '
                   'to increase its revenue per customer.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Push Notifications'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-onepager-case-study-de',
        'company': 'The Kooples Onepager',
        'title': 'The Kooples Onepager',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-kooples-de-sls',
        'key_metrics': 'How The Kooples increased revenue per customer by 89% through mobile '
                       'wallets — a one-page snapshot of the objectives, rollout, and results (90% '
                       'repeat purchase lift, 98% card retention).',
        'context': 'Discover how The Kooples uses Brevo, and more specifically the mobile wallet, '
                   'to increase its revenue per customer.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Push Notifications'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-kooples-onepager-case-study-es',
        'company': 'The Kooples Onepager',
        'title': 'The Kooples Onepager',
        'type': 'case_study',
        'language': 'ES',
        'industry': 'retail',
        'url': 'https://content.brevo.com/onepager-the-kooples-es-sls',
        'key_metrics': 'How The Kooples increased revenue per customer by 89% through mobile '
                       'wallets — a one-page snapshot of the objectives, rollout, and results (90% '
                       'repeat purchase lift, 98% card retention).',
        'context': 'Discover how The Kooples uses Brevo, and more specifically the mobile wallet, '
                   'to increase its revenue per customer.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Push Notifications'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-loyalty-loop-a-martech-guide-to-smart-loyalty-programs-e',
        'company': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'title': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'type': 'ebook',
        'language': 'EN',
        'industry': 'retail',
        'url': 'https://content.brevo.com/en-loyalty-loop-guide-26',
        'key_metrics': '88% of consumers trust recommendations from people they know more than any '
                       'other form of marketing (Nielsen) — this Brevo x chiefmartec guide '
                       'introduces "The Loyalty Flywheel," showing how smart loyalty programs turn '
                       'retention into a self-reinforcing acquisition engine, with digital wallets '
                       'as a key owned channel.',
        'context': 'Master summary:\n'
                   'The "Smart Loyalty Report 2026," authored by martech expert Scott Brinker, '
                   'provides a strategic guide on transforming traditional, transaction-based '
                   'points programs into dynamic, omnichannel "Smart Loyalty" engines. It explains '
                   'how loyalty programs must sit at the center of the martech orchestration layer '
                   'to unify data, leverage AI, and turn customer retention into a powerful '
                   'acquisition channel.Best use / When to share:\n'
                   'Share this during the Consideration or Decision stages with C-level '
                   'executives, CMOs, and Directors of Marketing or Martech who are evaluating '
                   'their retention strategies or CDP architecture. It is highly effective for '
                   'addressing pain points related to high customer acquisition costs (CAC), '
                   'disconnected martech silos, and the limitations of legacy "earn and burn" '
                   'loyalty programs.Key takeaways:\n'
                   '• Defines the shift from "Classic Loyalty" (purchases only) to "Smart Loyalty" '
                   '(rewarding social engagement, referrals, device interactions, and events).\n'
                   '• Introduces the "Loyalty Flywheel," demonstrating how rewarded advocacy turns '
                   'existing customers into a zero-CAC acquisition channel.\n'
                   '• Outlines the integration imperative: loyalty engines must connect seamlessly '
                   'with CDPs, campaign management, and AI agents to act on real-time intent '
                   'signals.\n'
                   '• Provides a "Smart Loyalty Scorecard" separating business value metrics '
                   '(e.g., incremental LTV, purchase frequency) from program vitality metrics '
                   '(e.g., active engagement, breakage rate).\n'
                   '• Explains why digital wallets (Apple/Google Wallet) are critical, '
                   'underutilized owned channels that bypass inbox competition.Search keywords:\n'
                   'smart loyalty, Scott Brinker, martech, loyalty flywheel, customer retention, '
                   'customer acquisition cost, CAC, LTV, loyalty engine, digital wallet, CDP, '
                   'artificial intelligence, omnichannel, program vitality, business value, '
                   'report, guide, loyalty strategyNotes & Status:\n'
                   'Authored by Scott Brinker (Chiefmartec). The content focuses heavily on '
                   'strategy and architecture rather than Brevo product specifics, making it an '
                   'excellent thought-leadership piece.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Program', 'Mobile Wallet', 'Marketing Automation', 'CDP'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'the-loyalty-loop-a-martech-guide-to-smart-loyalty-programs-e-2',
        'company': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'title': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'type': 'ebook',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/fr-smart-loyalty-guide',
        'key_metrics': '88% of consumers trust recommendations from people they know more than any '
                       'other form of marketing (Nielsen) — this Brevo x chiefmartec guide '
                       'introduces "The Loyalty Flywheel," showing how smart loyalty programs turn '
                       'retention into a self-reinforcing acquisition engine, with digital wallets '
                       'as a key owned channel.',
        'context': 'Master summary:\n'
                   'The "Smart Loyalty Report 2026," authored by martech expert Scott Brinker, '
                   'provides a strategic guide on transforming traditional, transaction-based '
                   'points programs into dynamic, omnichannel "Smart Loyalty" engines. It explains '
                   'how loyalty programs must sit at the center of the martech orchestration layer '
                   'to unify data, leverage AI, and turn customer retention into a powerful '
                   'acquisition channel.Best use / When to share:\n'
                   'Share this during the Consideration or Decision stages with C-level '
                   'executives, CMOs, and Directors of Marketing or Martech who are evaluating '
                   'their retention strategies or CDP architecture. It is highly effective for '
                   'addressing pain points related to high customer acquisition costs (CAC), '
                   'disconnected martech silos, and the limitations of legacy "earn and burn" '
                   'loyalty programs.Key takeaways:\n'
                   '• Defines the shift from "Classic Loyalty" (purchases only) to "Smart Loyalty" '
                   '(rewarding social engagement, referrals, device interactions, and events).\n'
                   '• Introduces the "Loyalty Flywheel," demonstrating how rewarded advocacy turns '
                   'existing customers into a zero-CAC acquisition channel.\n'
                   '• Outlines the integration imperative: loyalty engines must connect seamlessly '
                   'with CDPs, campaign management, and AI agents to act on real-time intent '
                   'signals.\n'
                   '• Provides a "Smart Loyalty Scorecard" separating business value metrics '
                   '(e.g., incremental LTV, purchase frequency) from program vitality metrics '
                   '(e.g., active engagement, breakage rate).\n'
                   '• Explains why digital wallets (Apple/Google Wallet) are critical, '
                   'underutilized owned channels that bypass inbox competition.Search keywords:\n'
                   'smart loyalty, Scott Brinker, martech, loyalty flywheel, customer retention, '
                   'customer acquisition cost, CAC, LTV, loyalty engine, digital wallet, CDP, '
                   'artificial intelligence, omnichannel, program vitality, business value, '
                   'report, guide, loyalty strategyNotes & Status:\n'
                   'Authored by Scott Brinker (Chiefmartec). The content focuses heavily on '
                   'strategy and architecture rather than Brevo product specifics, making it an '
                   'excellent thought-leadership piece.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Program', 'Mobile Wallet', 'Marketing Automation', 'CDP'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'the-loyalty-loop-a-martech-guide-to-smart-loyalty-programs-e-3',
        'company': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'title': 'The Loyalty Loop: A Martech Guide to Smart Loyalty Programs',
        'type': 'ebook',
        'language': 'DE',
        'industry': 'retail',
        'url': 'https://content.brevo.com/de-smart-loyalty-guide',
        'key_metrics': '88% of consumers trust recommendations from people they know more than any '
                       'other form of marketing (Nielsen) — this Brevo x chiefmartec guide '
                       'introduces "The Loyalty Flywheel," showing how smart loyalty programs turn '
                       'retention into a self-reinforcing acquisition engine, with digital wallets '
                       'as a key owned channel.',
        'context': 'Master summary:\n'
                   'The "Smart Loyalty Report 2026," authored by martech expert Scott Brinker, '
                   'provides a strategic guide on transforming traditional, transaction-based '
                   'points programs into dynamic, omnichannel "Smart Loyalty" engines. It explains '
                   'how loyalty programs must sit at the center of the martech orchestration layer '
                   'to unify data, leverage AI, and turn customer retention into a powerful '
                   'acquisition channel.Best use / When to share:\n'
                   'Share this during the Consideration or Decision stages with C-level '
                   'executives, CMOs, and Directors of Marketing or Martech who are evaluating '
                   'their retention strategies or CDP architecture. It is highly effective for '
                   'addressing pain points related to high customer acquisition costs (CAC), '
                   'disconnected martech silos, and the limitations of legacy "earn and burn" '
                   'loyalty programs.Key takeaways:\n'
                   '• Defines the shift from "Classic Loyalty" (purchases only) to "Smart Loyalty" '
                   '(rewarding social engagement, referrals, device interactions, and events).\n'
                   '• Introduces the "Loyalty Flywheel," demonstrating how rewarded advocacy turns '
                   'existing customers into a zero-CAC acquisition channel.\n'
                   '• Outlines the integration imperative: loyalty engines must connect seamlessly '
                   'with CDPs, campaign management, and AI agents to act on real-time intent '
                   'signals.\n'
                   '• Provides a "Smart Loyalty Scorecard" separating business value metrics '
                   '(e.g., incremental LTV, purchase frequency) from program vitality metrics '
                   '(e.g., active engagement, breakage rate).\n'
                   '• Explains why digital wallets (Apple/Google Wallet) are critical, '
                   'underutilized owned channels that bypass inbox competition.Search keywords:\n'
                   'smart loyalty, Scott Brinker, martech, loyalty flywheel, customer retention, '
                   'customer acquisition cost, CAC, LTV, loyalty engine, digital wallet, CDP, '
                   'artificial intelligence, omnichannel, program vitality, business value, '
                   'report, guide, loyalty strategyNotes & Status:\n'
                   'Authored by Scott Brinker (Chiefmartec). The content focuses heavily on '
                   'strategy and architecture rather than Brevo product specifics, making it an '
                   'excellent thought-leadership piece.',
        'pain_points': '',
        'brevo_features_tags': ['Loyalty Program', 'Mobile Wallet', 'Marketing Automation', 'CDP'],
        'best_for_verticals': ['retail', 'ecommerce'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program', 'needs_cdp'],
        'archetype_fit': ['Consolidator', 'Feature Specialist']},
    {   'id': 'the-power-of-customer-data-platforms-cdp-ebook-ebook-de',
        'company': 'The Power of Customer Data Platforms (CDP ebook)',
        'title': 'The Power of Customer Data Platforms (CDP ebook)',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-cdp-de-sls',
        'key_metrics': 'Only 31% of companies have a unified 360-degree view of their customer '
                       'data (Harvard Business Review) — and per McKinsey, brands using a CDP to '
                       'personalize pricing and offers see revenue per customer rise by more than '
                       '10%.',
        'context': 'This ebook is a general ebook on Customer Data Platforms: Find out what a CDP '
                   'is, how it works, what the difference between CDP, CRM and DWH is. See 12 use '
                   'cases what CDPs can be used for, including USPs why Brevo is the right CDP '
                   'choice for companies.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP',
                                   'Personalization',
                                   'Marketing Automation',
                                   'Data Unification'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'the-power-of-customer-data-platforms-cdp-ebook-ebook-en',
        'company': 'The Power of Customer Data Platforms (CDP ebook)',
        'title': 'The Power of Customer Data Platforms (CDP ebook)',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-cdp-en-sls',
        'key_metrics': 'Only 31% of companies have a unified 360-degree view of their customer '
                       'data (Harvard Business Review) — and per McKinsey, brands using a CDP to '
                       'personalize pricing and offers see revenue per customer rise by more than '
                       '10%.',
        'context': 'This ebook is a general ebook on Customer Data Platforms: Find out what a CDP '
                   'is, how it works, what the difference between CDP, CRM and DWH is. See 12 use '
                   'cases what CDPs can be used for, including USPs why Brevo is the right CDP '
                   'choice for companies.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP',
                                   'Personalization',
                                   'Marketing Automation',
                                   'Data Unification'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'the-power-of-customer-data-platforms-cdp-ebook-ebook-fr',
        'company': 'The Power of Customer Data Platforms (CDP ebook)',
        'title': 'The Power of Customer Data Platforms (CDP ebook)',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-cdp-fr-sls',
        'key_metrics': 'Only 31% of companies have a unified 360-degree view of their customer '
                       'data (Harvard Business Review) — and per McKinsey, brands using a CDP to '
                       'personalize pricing and offers see revenue per customer rise by more than '
                       '10%.',
        'context': 'This ebook is a general ebook on Customer Data Platforms: Find out what a CDP '
                   'is, how it works, what the difference between CDP, CRM and DWH is. See 12 use '
                   'cases what CDPs can be used for, including USPs why Brevo is the right CDP '
                   'choice for companies.',
        'pain_points': '',
        'brevo_features_tags': [   'CDP',
                                   'Personalization',
                                   'Marketing Automation',
                                   'Data Unification'],
        'best_for_verticals': [],
        'best_for_signals': ['needs_cdp'],
        'archetype_fit': ['Consolidator']},
    {   'id': 'the-ultimate-guide-for-push-notifications-ebook-fr',
        'company': 'The Ultimate Guide for Push notifications',
        'title': 'The Ultimate Guide for Push notifications',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/guide-ultime-push-notifications-fr-sls',
        'key_metrics': 'Push notifications drive a 30% return rate among notified users and double '
                       'page views versus non-notified visitors — this guide breaks down why 15% '
                       'of top websites already use them and how to build a high-converting push '
                       'strategy.',
        'context': 'In this ebook, we dive into the power of push notifications and discover why '
                   'and how they represent a real opportunity to enrich the user experience, '
                   'strengthen customer engagement, and boost sales performance. Recommended asset '
                   'for both Sales follow ups and ENT marketing activities (Field & Growth).',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Web Push',
                                   'Customer Engagement',
                                   'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-ultimate-guide-for-push-notifications-ebook-en',
        'company': 'The Ultimate Guide for Push notifications',
        'title': 'The Ultimate Guide for Push notifications',
        'type': 'ebook',
        'language': 'EN',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-ultimate-guide-push-notifications-en-sls',
        'key_metrics': 'Push notifications drive a 30% return rate among notified users and double '
                       'page views versus non-notified visitors — this guide breaks down why 15% '
                       'of top websites already use them and how to build a high-converting push '
                       'strategy.',
        'context': 'In this ebook, we dive into the power of push notifications and discover why '
                   'and how they represent a real opportunity to enrich the user experience, '
                   'strengthen customer engagement, and boost sales performance. Recommended asset '
                   'for both Sales follow ups and ENT marketing activities (Field & Growth).',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Web Push',
                                   'Customer Engagement',
                                   'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'the-ultimate-guide-for-push-notifications-ebook-de',
        'company': 'The Ultimate Guide for Push notifications',
        'title': 'The Ultimate Guide for Push notifications',
        'type': 'ebook',
        'language': 'DE',
        'industry': '',
        'url': 'https://content.brevo.com/de-leitfaden-push-benachrichtigungen-2024-sls',
        'key_metrics': 'Push notifications drive a 30% return rate among notified users and double '
                       'page views versus non-notified visitors — this guide breaks down why 15% '
                       'of top websites already use them and how to build a high-converting push '
                       'strategy.',
        'context': 'In this ebook, we dive into the power of push notifications and discover why '
                   'and how they represent a real opportunity to enrich the user experience, '
                   'strengthen customer engagement, and boost sales performance. Recommended asset '
                   'for both Sales follow ups and ENT marketing activities (Field & Growth).',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Web Push',
                                   'Customer Engagement',
                                   'Mobile Marketing'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'trusted-shops-reactivates-21-of-unengaged-contacts-thanks-to',
        'company': 'Trusted Shops Reactivates 21% of Unengaged Contacts Thanks to Marketing '
                   'Automation',
        'title': 'Trusted Shops Reactivates 21% of Unengaged Contacts Thanks to Marketing '
                 'Automation',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'ecommerce',
        'url': 'https://www.brevo.com/success-stories/trusted-shops/',
        'key_metrics': 'This German trust-mark/buyer-protection company reactivated 21% of '
                       'unengaged subscribers with a single 3-step automation workflow -- while '
                       'keeping newsletter open rates above 30% (36% on one edition) and '
                       'unsubscribe rates as low as 0.15%, fully GDPR-compliant on EU-hosted '
                       'servers.',
        'context': 'This German trust-mark/buyer-protection company reactivated 21% of unengaged '
                   'subscribers with a single 3-step automation workflow -- while keeping '
                   'newsletter open rates above 30% (36% on one edition) and unsubscribe rates as '
                   'low as 0.15%, fully GDPR-compliant on EU-hosted servers.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation (reactivation workflows)',
                                   'Dynamic Content + Segmentation',
                                   'GDPR/EU Data Hosting',
                                   'Newsletter/Email Marketing'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'trusted-shops-reactivates-21-of-unengaged-contacts-thanks-to-2',
        'company': 'Trusted Shops Reactivates 21% of Unengaged Contacts Thanks to Marketing '
                   'Automation',
        'title': 'Trusted Shops Reactivates 21% of Unengaged Contacts Thanks to Marketing '
                 'Automation',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://www.brevo.com/de/success-stories/trusted-shops/',
        'key_metrics': 'This German trust-mark/buyer-protection company reactivated 21% of '
                       'unengaged subscribers with a single 3-step automation workflow -- while '
                       'keeping newsletter open rates above 30% (36% on one edition) and '
                       'unsubscribe rates as low as 0.15%, fully GDPR-compliant on EU-hosted '
                       'servers.',
        'context': 'This German trust-mark/buyer-protection company reactivated 21% of unengaged '
                   'subscribers with a single 3-step automation workflow -- while keeping '
                   'newsletter open rates above 30% (36% on one edition) and unsubscribe rates as '
                   'low as 0.15%, fully GDPR-compliant on EU-hosted servers.',
        'pain_points': '',
        'brevo_features_tags': [   'Marketing Automation (reactivation workflows)',
                                   'Dynamic Content + Segmentation',
                                   'GDPR/EU Data Hosting',
                                   'Newsletter/Email Marketing'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Consolidator']},
    {   'id': 'use-case-adopt-x-wallet-case-study-fr',
        'company': 'Use Case : Adopt x Wallet',
        'title': 'Use Case : Adopt x Wallet',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/use-case-adopt-fr-sls',
        'key_metrics': 'Adopt Parfums turned its loyalty card into a mobile wallet channel, '
                       'sending 5-star-rated push notifications for birthday rewards and new '
                       "launches — customers say it's faster at checkout and keeps them coming "
                       'back to discover new products.',
        'context': 'How does Adopt Parfums use the wallet as a new channel to boost customer '
                   'engagement? Discover the Wallet Strategy of the Adopt Parfums Brand: '
                   'acquisition and digitization strategies for the loyalty progra & the different '
                   'channels the brand uses to reach its customers via the Mobile Wallet.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Push Notifications', 'Retail'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'use-case-maison-123-x-wallet-case-study-fr',
        'company': 'Use Case : Maison 123 x Wallet',
        'title': 'Use Case : Maison 123 x Wallet',
        'type': 'case_study',
        'language': 'FR',
        'industry': 'retail',
        'url': 'https://content.brevo.com/use-case-maison-123-fr-sls',
        'key_metrics': 'Maison 123 doubled (x2) its revenue per customer after adding a mobile '
                       'wallet loyalty card — a clear real-world example of wallet-based loyalty '
                       'outperforming traditional cards for driving repeat purchases.',
        'context': 'Maison 123 was looking for a more eco-friendly communication method than '
                   'print, one that aligns with the habits of its customers. A channel that is '
                   'both more modern and enables maintaining a connection with customers through '
                   'push notifications : \n'
                   'Maison 123 chose the wallet.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Loyalty Program', 'Retail', 'Ecommerce'],
        'best_for_verticals': ['retail'],
        'best_for_signals': ['has_wallet', 'has_loyalty_program'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'vekoop-de-startet-durch-mit-e-mail-marketing-und-erreicht-so',
        'company': 'Vekoop.de startet durch mit E-Mail Marketing und erreicht so eine '
                   'Zustellbarkeitsrate von 98',
        'title': 'Vekoop.de startet durch mit E-Mail Marketing und erreicht so eine '
                 'Zustellbarkeitsrate von 98,77 %',
        'type': 'case_study',
        'language': 'DE',
        'industry': 'ecommerce',
        'url': 'https://www.brevo.com/de/success-stories/vekoop-de/',
        'key_metrics': 'This German vegan e-commerce shop hit a 98.77% email deliverability rate '
                       "with Brevo's drag-and-drop newsletter builder -- after a plug-and-play "
                       'integration via their JTL shop system, with marketing automation and live '
                       'chat next on their roadmap.',
        'context': 'This German vegan e-commerce shop hit a 98.77% email deliverability rate with '
                   "Brevo's drag-and-drop newsletter builder -- after a plug-and-play integration "
                   'via their JTL shop system, with marketing automation and live chat next on '
                   'their roadmap.',
        'pain_points': '',
        'brevo_features_tags': [   'Email Marketing',
                                   'Drag-and-Drop Editor',
                                   'Ecommerce Integration (JTL)',
                                   'Deliverability',
                                   'GDPR Compliance'],
        'best_for_verticals': ['ecommerce'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']},
    {   'id': 'wallet-barometer-2025-ebook-fr',
        'company': 'Wallet Barometer 2025',
        'title': 'Wallet Barometer 2025',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-barometre-wallet-2025-fr-sls',
        'key_metrics': '54% of French consumers now recognize wallet apps, up from 50% in 2024 — '
                       'and among 50-64 year-olds, awareness jumped 10 points in a single year, '
                       'showing mobile wallets are moving fast beyond early adopters into the '
                       'mainstream.',
        'context': '1. Master Summary\n'
                   "This is Brevo's second-edition Mobile Wallet Barometer (2025), an original "
                   'research report produced in partnership with Ifop based on a survey of 1,007 '
                   'representative French adults. It documents the growing adoption, perceived '
                   'utility, and usage patterns of mobile wallet applications (Apple Wallet and '
                   'Google Wallet) in France. The core value proposition is that Brevo positions '
                   'itself as the leading wallet marketing expert in France, backed by proprietary '
                   'data that prospects and clients cannot find elsewhere.\n'
                   '2. Search Keywords & AI Tags\n'
                   'wallet mobile, Apple Wallet, Google Wallet, cartes de fidélité, push '
                   'notifications, marketing mobile, fidélisation, baromètre, étude consommateurs, '
                   'France, retail, omnicanal, engagement client, dématérialisation, génération Z\n'
                   '3. Sales Context: When to Share This\n'
                   'Use this asset at any stage of the sales cycle where wallet marketing is '
                   'relevant:\n'
                   '• Discovery / awareness stage with retail, e-commerce, transport, or '
                   'loyalty-heavy prospects who are not yet using wallet — cite adoption stats '
                   '(41% of French consumers now use a wallet app, +7 pts vs 2024) to build '
                   'urgency.\n'
                   '• Demo / proposal stage with Pro or Enterprise prospects managing loyalty '
                   'programs — use the 85% loyalty card penetration figure and the 37.8M active '
                   "wallet cards on Brevo's platform to validate scale and credibility.\n"
                   '• Objection handling when a prospect questions wallet ROI or channel relevance '
                   '— the 47% push notification influence rate and the 71% utility recognition '
                   'rate are strong counters.\n'
                   "• Cross-sell / upsell with existing email or SMS clients who haven't activated "
                   'Wallet — the data shows wallet is becoming a standard in omnichannel '
                   'strategy.\n'
                   'Example phrasing: "Our latest study shows 71% of French consumers now see '
                   'wallet as useful for managing their loyalty programs — up 6 points in one '
                   'year. Here\'s the full data."\n'
                   '4. Key Takeaways\n'
                   '• Wallet awareness in France has reached 54% (+4 pts YoY), with particularly '
                   'strong uptake among 18–24-year-olds (82%) — confirming that wallet is becoming '
                   'mainstream, not niche.\n'
                   '• Perceived utility is growing fast: 71% of French consumers find having all '
                   'loyalty cards in one mobile app useful (+6 pts), and 84% of 18–49-year-olds '
                   'share this view.\n'
                   '• Loyalty cards remain the dominant wallet content (85%), but payment cards '
                   '(48%, +6 pts) and transport tickets (35%, +4 pts) are growing fast — wallet is '
                   'evolving into a full daily-use tool.\n'
                   '• Push notifications remain an effective engagement lever: 47% of French '
                   'consumers say they influence their purchase behavior, rising to 57% among '
                   '25–34-year-olds.\n'
                   '• French consumers are enrolled in fewer loyalty programs on average (5.6 vs 6 '
                   'in 2024), signaling growing selectivity — brands must offer superior, '
                   'centralized experiences to stay relevant.\n'
                   '5. Key KPIs, Figures & Insights\n'
                   '• Wallet awareness (France, 2025): 54% — up from 50% in 2024 (+4 pts)\n'
                   '• Wallet awareness, 18–24-year-olds: 82% — up from 71% in 2024 (+11 pts)\n'
                   '• Wallet awareness, 65+ year-olds: 29% — down from 34% in 2024 (–5 pts)\n'
                   '• Perceived utility (all French consumers): 71% — up from 65% in 2024 (+6 '
                   'pts)\n'
                   '• Perceived utility, 18–49-year-olds: 84% — up from 81% in 2024 (+3 pts)\n'
                   '• Perceived utility, 50–64-year-olds: 66% — up from 56% in 2024 (+10 pts)\n'
                   '• Perceived utility, 65+ year-olds: 51% — up from 45% in 2024 (+6 pts)\n'
                   '• Merchant recognition of wallet utility: 75%\n'
                   '• Active wallet cards on Brevo platform (July 2025): 37.8 million\n'
                   '• Wallet usage rate (France, 2025): 41% — up from 34% in 2024 (+7 pts)\n'
                   '• Wallet usage rate, 18–24-year-olds: 60%\n'
                   '• Average card types per wallet user: 2\n'
                   '• Top wallet content — loyalty cards: 85% (–1 pt)\n'
                   '• Payment cards in wallet: 48% (+6 pts vs 42% in 2024)\n'
                   '• Transport/travel tickets in wallet: 35% (+4 pts)\n'
                   '• Event tickets in wallet: 19% (stable)\n'
                   '• Coupons/vouchers in wallet: 20% (–3 pts)\n'
                   '• Push notification influence rate (all): 47%\n'
                   '• Push notification influence rate, 25–34-year-olds: 57%\n'
                   '• "Completely influenced" by push notifications: 21% (+5 pts YoY)\n'
                   '• "Not at all influenced" by push notifications: 23%\n'
                   '• Primary wallet use — identification at POS/transport/events: 52% (vs 58% in '
                   '2024)\n'
                   '• Primary wallet use — quick access to loyalty data: 52% (vs 57% in 2024)\n'
                   '• Wallet use for in-store payment: 42% (vs 37% in 2024, +5 pts)\n'
                   '• Average loyalty program enrollments per consumer: 5.6 (vs 6 in 2024)\n'
                   '• Survey sample: 1,007 adults, representative of the French population 18+, '
                   'conducted online May 21–23, 2025 (Ifop for Brevo)\n'
                   '6. Product Accuracy Check\n'
                   'The asset references Apple Wallet (called "Cartes" in the French iOS '
                   "interface) and Google Wallet — both current and correctly named. Brevo's "
                   'wallet product and platform are referenced in line with current positioning. '
                   'The 37.8M active wallet cards figure is presented as a July 2025 data point, '
                   "which is internally consistent with the report's publication timeline.\n"
                   'No references to "Sendinblue," deprecated feature names, or outdated pricing '
                   'tiers. Product details appear up to date based on current knowledge.\n'
                   '———————-\n'
                   'The 2025 Mobile Wallet Barometer is our second annual survey measuring wallet '
                   'adoption and usage in France. This Ifop study provides key market intelligence '
                   'on consumer awareness, perceived utility, and usage patterns of mobile wallet '
                   'applications. It highlights the growing acceptance across generations, '
                   'evolving use cases beyond loyalty cards, and effectiveness of push '
                   'notifications.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Market Research', 'Consumer Trends'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'wallet-barometer-ebook-ebook-fr',
        'company': 'Wallet Barometer Ebook',
        'title': 'Wallet Barometer Ebook',
        'type': 'ebook',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/ebook-barometre-wallet-fr-sls',
        'key_metrics': 'Wallet app awareness among French consumers grew from 38.7% to 50% in just '
                       "three years (+29%) — and major brands like Lacoste, McDonald's, and "
                       'Sephora are already capitalizing on the trend, per this Ifop survey '
                       'commissioned by Brevo.',
        'context': "A study carried out in partnership with IFOP on French consumers' knowledge, "
                   'use and perceptions of the mobile wallet.',
        'pain_points': '',
        'brevo_features_tags': ['Mobile Wallet', 'Market Research', 'Consumer Trends'],
        'best_for_verticals': [],
        'best_for_signals': ['has_wallet'],
        'archetype_fit': ['Feature Specialist', 'Saver']},
    {   'id': 'webpush-case-study-2024-case-study-fr',
        'company': 'WebPush Case Study - 2024',
        'title': 'WebPush Case Study - 2024',
        'type': 'case_study',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/use-case-webpush-fr-sls',
        'key_metrics': 'See how major French retailers like Au Forum du Bâtiment, SoBrico, and '
                       'Transavia use web push notifications for cart-abandonment recovery, '
                       'new-account incentives, and personalized product discovery — real send '
                       'examples and opt-in designs included.',
        'context': '[For INTERNAL use only]\n'
                   'Push notifications: Success stories from companies that turn engagement into '
                   'conversion.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Web Push',
                                   'Ecommerce',
                                   'Customer Engagement'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'webpush-case-study-2025-case-study-fr',
        'company': 'WebPush Case Study - 2025',
        'title': 'WebPush Case Study - 2025',
        'type': 'case_study',
        'language': 'FR',
        'industry': '',
        'url': 'https://content.brevo.com/usecase-webpush2025-fr-sls',
        'key_metrics': 'This expanded success-story collection adds Emirates Holidays and ByMyCar '
                       "to Brevo's web push playbook — showing how travel and auto brands "
                       "re-engage shoppers on products they viewed but didn't buy, no email "
                       'address required.',
        'context': '[For INTERNAL use only]\n'
                   'WebPush notifications: Success stories from companies that turn engagement '
                   'into conversion.',
        'pain_points': '',
        'brevo_features_tags': [   'Push Notifications',
                                   'Web Push',
                                   'Retargeting',
                                   'Ecommerce',
                                   'Travel'],
        'best_for_verticals': [],
        'best_for_signals': [],
        'archetype_fit': ['Feature Specialist']},
    {   'id': 'yumpingo-increases-survey-click-rates-by-14-after-upgrading-',
        'company': 'Yumpingo increases survey click rates by 14% after upgrading to BrevoPlus',
        'title': 'Yumpingo increases survey click rates by 14% after upgrading to BrevoPlus',
        'type': 'case_study',
        'language': 'EN',
        'industry': 'hospitality',
        'url': 'https://www.brevo.com/success-stories/yumpingo/',
        'key_metrics': 'This UK hospitality CX platform saw Microsoft B2C open rates jump from '
                       '12.5% to nearly 35% (+180% in 10 days) after upgrading to Brevo Enterprise '
                       'and reconfiguring sending domains -- plus a 14% lift in survey '
                       'click-through rate and 99%+ Yahoo deliverability.',
        'context': 'This UK hospitality CX platform saw Microsoft B2C open rates jump from 12.5% '
                   'to nearly 35% (+180% in 10 days) after upgrading to Brevo Enterprise and '
                   'reconfiguring sending domains -- plus a 14% lift in survey click-through rate '
                   'and 99%+ Yahoo deliverability.',
        'pain_points': '',
        'brevo_features_tags': [   'Enterprise Plan / Deliverability Consulting',
                                   'Domain/IP Reconfiguration',
                                   'Dedicated Deliverability Support',
                                   'Email Marketing'],
        'best_for_verticals': ['hospitality'],
        'best_for_signals': [],
        'archetype_fit': ['Email Specialist']}]


# ── Market -> resource language mapping ───────────────────────────────────────
_MARKET_LANGUAGE: dict[str, str] = {
    "FR": "FR",
    "DE": "DE", "AT": "DE", "CH": "DE",
}


def _resource_language(market: str) -> str:
    return _MARKET_LANGUAGE.get((market or "").strip(), "EN")


# ── Tool definition (unused directly — kept for reference; see module
# docstring for why resource selection is pre-filtered in Python instead) ─────

RESOURCE_TOOL_DEFINITION: dict[str, Any] = {
    "name": "search_brevo_resources",
    "description": (
        "Returns all available Brevo case studies, reports, and ebooks. "
        "Review every resource in the result and select the SINGLE most relevant one "
        "for this contact, based on their vertical, signal flags (loyalty/CDP/wallet), "
        "and the resource selection rules defined in each email section of the prompt. "
        "Use the selected resource to populate all resource.* fields when generating content."
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
    return RESOURCES


def shortlist_resources(company: dict, market: str, icp_archetype: str = "", n_per_type: int = 4) -> list[dict[str, Any]]:
    """Pre-filters the 241-resource catalogue down to a small, relevant shortlist
    before it's injected into the content-generation prompt — at this scale,
    dumping the full catalogue into every request would be a large, costly
    injection every single call. Scoring priority: resource language matches
    the contact's market (hard filter, falls back to EN if nothing matches) >
    vertical match > signal overlap (has_wallet/has_loyalty_program/needs_cdp)
    > archetype fit. Returns up to n_per_type case_study + n_per_type
    non-case_study (ebook) resources so Email 2 (needs a case_study) and
    Email 3 (needs a report/ebook, different from Email 2) always have
    genuine options to choose between.
    """
    lang = _resource_language(market)
    vertical = (company.get("vertical") or "").lower()

    active_signals: set[str] = set()
    if company.get("has_loyalty_program"): active_signals.add("has_loyalty_program")
    if company.get("has_wallet"):          active_signals.add("has_wallet")
    if company.get("needs_cdp"):           active_signals.add("needs_cdp")

    archetype = (icp_archetype or "").strip()

    def _score(r: dict) -> tuple[int, int, int, int]:
        lang_score      = 1 if r["language"] == lang else 0
        vert_score      = sum(1 for v in r["best_for_verticals"] if v in vertical or vertical in v)
        signal_score    = len(active_signals & set(r["best_for_signals"]))
        archetype_score = 1 if archetype and archetype in r["archetype_fit"] else 0
        return (lang_score, vert_score, signal_score, archetype_score)

    pool = RESOURCES
    lang_pool = [r for r in pool if r["language"] == lang]
    if not lang_pool:
        lang_pool = [r for r in pool if r["language"] == "EN"]

    case_studies = sorted(
        (r for r in lang_pool if r["type"] == "case_study"),
        key=_score, reverse=True,
    )[:n_per_type]
    ebooks = sorted(
        (r for r in lang_pool if r["type"] != "case_study"),
        key=_score, reverse=True,
    )[:n_per_type]

    return case_studies + ebooks
