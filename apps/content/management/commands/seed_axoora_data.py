from django.core.management.base import BaseCommand
from apps.content.models import HeroConfiguration, JournalArticle, FaqItem, MerchantStory, ProductItem
from apps.waitlist.models import WaitlistLead


class Command(BaseCommand):
    help = 'Seeds initial Axoora platform data including CMS content, FAQs, articles, and sample leads.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Axoora initial platform data...")

        # 1. Hero Configuration
        hero = HeroConfiguration.get_or_create_config()
        self.stdout.write(self.style.SUCCESS("✓ Hero configuration seeded."))

        # 2. Journal Articles
        articles_data = [
            {
                'slug': 'designing-resilient-nibss-payment-rails',
                'category': 'Engineering',
                'title': 'Designing resilient NIBSS payment rails for intermittent networks',
                'summary': 'How our engineering team built idempotent retry mechanisms and offline-tolerant handshakes that settle transfers across erratic rural cellular signals.',
                'content': 'Nigeria’s electronic payment system relies heavily on NIP (NIBSS Instant Payment) protocols. In dense commercial hubs like Wuse Market or outdoor stalls, intermittent cellular coverage frequently causes dropouts midway through transaction requests. This article breaks down how Axoora implements cryptographic state preservation, dual-SIM network failover, and idempotent reconciliation workers to ensure zero double-debits.',
                'read_time': '6 min read',
                'author': 'Axoora Architecture Group',
                'published_date': 'September 2026',
            },
            {
                'slug': 'sharia-compliant-treasury-architecture',
                'category': 'Business',
                'title': 'The architecture of a true non-interest corporate treasury',
                'summary': 'A technical look at how we isolate deposits from speculative debt markets to guarantee 100% Sharia-compliant business banking and safe custody.',
                'content': 'Conventional fintech accounts often pool idle funds into debt-backed money market instruments. Axoora separates funds into dedicated sovereign custodial vaults governed by Sharia audit logs, ensuring no interest or riba is generated or accrued on customer accounts.',
                'read_time': '5 min read',
                'author': 'Finance & Compliance Guild',
                'published_date': 'August 2026',
            },
            {
                'slug': 'conversational-banking-llm-whatsapp',
                'category': 'Technology',
                'title': 'Bringing sovereign banking to WhatsApp through conversational AI',
                'summary': 'Why the future of African commerce isn’t inside another 100MB native app, but directly inside the messaging surface merchants already live in every day.',
                'content': 'Over 90% of Nigerian small businesses negotiate sales and close invoices on WhatsApp. We explain how Axoora AI operates natively within WhatsApp with multi-factor biometric session tokens and end-to-end encryption.',
                'read_time': '4 min read',
                'author': 'Axoora AI Research',
                'published_date': 'October 2026',
            },
            {
                'slug': 'practical-guide-retail-cashflow-abujan-markets',
                'category': 'Guides',
                'title': 'The practical guide to managing daily cashflow in bustling markets',
                'summary': 'Five actionable habits modern shop owners in Maitama, Utako, and Balogun use to automate staff reconciliations and stop inventory leaks.',
                'content': 'A comprehensive handbook for shop managers on separating personal cash from business cash using dedicated store NUBANs and dual-SIM Apex POS terminals.',
                'read_time': '8 min read',
                'author': 'Merchant Operations Team',
                'published_date': 'July 2026',
            },
        ]

        for item in articles_data:
            JournalArticle.objects.update_or_create(
                slug=item['slug'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(articles_data)} Journal articles seeded."))

        # 3. FAQs
        faqs_data = [
            {
                'question': 'What is Axoora?',
                'answer': 'Axoora is a Nigerian financial institution licensed by the Central Bank of Nigeria (CBN). Eligible deposits are insured by NDIC. We provide personal banking with Axoora AI, business accounts for shops, and POS solutions for agents.',
                'category': 'General',
                'order': 1,
            },
            {
                'question': 'Can I open an account or transfer money directly on this website?',
                'answer': 'No. This website is how people meet Axoora. People do not open accounts or send money in the browser. You can join our priority waitlist to be notified when live, download our mobile app, or bank with Axoora AI on WhatsApp.',
                'category': 'General',
                'order': 2,
            },
            {
                'question': 'What does "Bank with Axoora AI on WhatsApp" mean?',
                'answer': 'Our official WhatsApp channel (+234 911 000 2966) is Axoora AI on WhatsApp — personal banking built so you can send money, check balances, save, and ask questions directly in a chat just as you would in the app.',
                'category': 'Personal & Cards',
                'order': 3,
            },
            {
                'question': 'How fast do money transfers settle across Nigerian banks?',
                'answer': 'Transfers execute over direct NIBSS Instant Payment (NIP) rails with dual-redundant routing, settling in under 3 seconds with idempotent zero-double-debit safety.',
                'category': 'Personal & Cards',
                'order': 4,
            },
            {
                'question': 'Will Axoora ever ask for my PIN or password?',
                'answer': 'NEVER. We will never ask for your PIN, OTP, BVN, or password on this website, on WhatsApp, or by phone. If anyone asks you for a PIN pretending to be Axoora, notify support@axoora.ai immediately.',
                'category': 'Security',
                'order': 5,
            },
            {
                'question': 'What is Save and Earn, and is it interest-based?',
                'answer': 'Save and Earn means putting money aside and receiving a return that is strictly Islamic-compliant — no interest, no riba. Returns are generated through ethical asset-backed trade principles.',
                'category': 'Save and Earn',
                'order': 6,
            },
            {
                'question': 'What happens if a POS terminal encounters poor cellular signal?',
                'answer': 'The Axoora Apex POS terminal is built with dual active 4G SIM slots (MTN and Airtel/Glo) that auto-failover without dropping a transaction.',
                'category': 'Business & POS',
                'order': 7,
            },
        ]

        for item in faqs_data:
            FaqItem.objects.update_or_create(
                question=item['question'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(faqs_data)} FAQ items seeded."))

        # 4. Merchant Stories
        stories_data = [
            {
                'name': 'Hajia Fatima Al-Hassan',
                'role': 'Founder & Creative Director',
                'location': 'Maitama, Abuja',
                'quote': 'Before Axoora, separating my personal savings from textile inventory cash was a headache. Now, every payment into my shop NUBAN is accounted for instantly without network delays.',
                'stat_label': 'Monthly Turnover Settled',
                'stat_value': '₦18.4M+',
                'badge': 'Verified Luxury Retailer',
                'accent_color': '#10B981',
                'featured': True,
                'order': 1,
            },
            {
                'name': 'Chinedu Eze',
                'role': 'Wholesale Electronics Distributor',
                'location': 'Utako Market, Abuja',
                'quote': 'The dual-SIM on the Apex POS terminal is a game changer. During peak market hours when other networks hang, my terminal switches networks and prints receipts in 2 seconds.',
                'stat_label': 'Terminal Uptime Rate',
                'stat_value': '99.8%',
                'badge': 'High-Volume Agent',
                'accent_color': '#3B82F6',
                'featured': True,
                'order': 2,
            },
            {
                'name': 'Dr. Amina Bello',
                'role': 'Pediatric Clinic Administrator',
                'location': 'Wuse II, Abuja',
                'quote': 'Ethical, zero-interest custody for our clinic reserves gives our board complete peace of mind. Axoora is banking that respects our values.',
                'stat_label': 'Operational Peace of Mind',
                'stat_value': '100% Halal',
                'badge': 'Healthcare Partner',
                'accent_color': '#F59E0B',
                'featured': True,
                'order': 3,
            },
        ]

        for item in stories_data:
            MerchantStory.objects.update_or_create(
                name=item['name'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(stories_data)} Merchant stories seeded."))

        # 5. Product Catalog
        products_data = [
            {
                'name': 'Axoora Personal Account',
                'category': 'personal',
                'headline': 'Zero Transfer Fee Personal Banking & WhatsApp AI',
                'fee_structure': '₦0 transfers forever',
                'status': 'active',
                'highlight': 'WhatsApp Concierge',
                'description': 'Smart personal banking with instant NIP transfers, virtual dollar cards, and non-interest Save & Earn pools.',
                'order': 1,
            },
            {
                'name': 'Shop Dedicated NUBAN',
                'category': 'business',
                'headline': 'Separate Store Money From Personal Life',
                'fee_structure': 'Transparent 0.2% cap',
                'status': 'active',
                'highlight': 'Sub-accounts for staff',
                'description': 'Dedicated business account for shops and merchants with multi-user permissions and automatic bookkeeping reconciliations.',
                'order': 2,
            },
            {
                'name': 'Axoora Apex 4G POS Terminal',
                'category': 'pos',
                'headline': 'Dual-SIM 4G Intelligent Payment Hardware',
                'fee_structure': 'Lowest industry MDR',
                'status': 'active',
                'highlight': 'Instant 0s Settlement',
                'description': 'High-speed touch terminal with dual active MTN + Airtel eSIM failover and instant audio receipt alerts.',
                'order': 3,
            },
            {
                'name': 'Murabaha Inventory Financing',
                'category': 'capital',
                'headline': 'Non-Interest Ethical Working Capital for Verified Merchants',
                'fee_structure': 'Cost-plus transparent markup',
                'status': 'beta',
                'highlight': '0% Riba Interest',
                'description': 'Asset-backed inventory funding based on real transactional velocity rather than predatory debt.',
                'order': 4,
            },
        ]

        for item in products_data:
            ProductItem.objects.update_or_create(
                name=item['name'],
                defaults=item,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(products_data)} Products seeded."))

        # 6. Sample Waitlist Leads for Testing
        sample_leads = [
            {
                'full_name': 'Ibrahim Musa',
                'whatsapp_number': '+2348031234567',
                'email': 'ibrahim.m@example.com',
                'city': 'Abuja',
                'state': 'FCT',
                'business_name': 'Al-Noor Textiles',
                'interest': 'business',
                'status': 'approved',
                'notes': 'Requested 2 Apex POS terminals for Maitama store.',
            },
            {
                'full_name': 'Ngozi Okeke',
                'whatsapp_number': '+2348129876543',
                'email': 'ngozi.o@example.com',
                'city': 'Lagos',
                'state': 'Lagos',
                'interest': 'personal',
                'status': 'new',
                'notes': 'Interested in virtual dollar card and Save & Earn.',
            },
            {
                'full_name': 'Kabir Usman',
                'whatsapp_number': '+2349051122334',
                'email': 'kabir.u@example.com',
                'city': 'Kano',
                'state': 'Kano',
                'interest': 'pos-agent',
                'status': 'contacted',
                'notes': 'Agent aggregator managing 15 neighborhood kiosks.',
            },
        ]

        for lead in sample_leads:
            WaitlistLead.objects.get_or_create(
                email=lead['email'],
                defaults=lead,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(sample_leads)} Sample waitlist leads seeded."))
        self.stdout.write(self.style.SUCCESS("All Axoora initial platform data seeded successfully!"))
