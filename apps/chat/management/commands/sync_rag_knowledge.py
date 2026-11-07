from django.core.management.base import BaseCommand
from apps.chat.models import KnowledgeDocument, KnowledgeChunk
from apps.content.models import FaqItem, JournalArticle, ProductItem


class Command(BaseCommand):
    help = 'Populates and indexes the RAG knowledge documents and knowledge chunks.'

    def handle(self, *args, **options):
        self.stdout.write("Synchronizing Axoora RAG Knowledge Base...")

        # 1. Authoritative Core Knowledge Documents
        core_documents = [
            {
                'slug': 'apex-pos-technical-manual',
                'title': 'Axoora Apex 4G POS Terminal Specifications & Settlement Manual',
                'category': 'pos_hardware',
                'content': (
                    "The Axoora Apex POS terminal is an enterprise dual-SIM 4G payment hardware designed for Nigerian merchants, "
                    "agents, and high-volume retail hubs. Key features:\n"
                    "• Network Connectivity: Dual active eSIM slots (MTN and Airtel/Glo auto-failover) ensuring transactions never hang in poor signal markets.\n"
                    "• Settlement Speed: Instant zero-second (0s) direct NIBSS settlement to merchant shop accounts.\n"
                    "• Pricing & Fees: Lowest industry MDR capped at a flat 0.4% with ₦0 terminal maintenance charge.\n"
                    "• Offline Tolerance: Cryptographic local transaction buffering allows queue processing during temporary network outages.\n"
                    "• Battery & Hardware: 5200mAh all-day commercial battery, high-speed thermal receipt printer, and high-volume loud audio confirmation alerts.\n"
                    "• Delivery: Guaranteed nationwide dispatch within 48 hours to any Nigerian state from our Maitama distribution center."
                ),
            },
            {
                'slug': 'islamic-banking-halal-principles',
                'title': 'Non-Interest Islamic Banking & Ethical Custody Framework',
                'category': 'islamic_banking',
                'content': (
                    "Axoora operates strictly on certified non-interest Islamic finance principles (Sharia-compliant banking):\n"
                    "• 0% Riba (Zero Interest): We do not charge interest on accounts or borrow/lend customer deposits on speculative debt instruments.\n"
                    "• Safe Custody: All deposits are segregated in sovereign custodial vaults and insured by the Nigeria Deposit Insurance Corporation (NDIC).\n"
                    "• Save & Earn Vaults: Built upon ethical Mudarabah (profit-sharing) and Murabaha (cost-plus asset trade). Returns come from real tangible commerce, never debt interest.\n"
                    "• Paycircle (Digital Ajo / Esusu): Rotating group contribution circles built directly into the app and WhatsApp with zero hidden deduction fees."
                ),
            },
            {
                'slug': 'transfer-dispute-resolution-protocol',
                'title': 'NIBSS Instant Payment Rails, Interbank Transfers & Dispute Resolution',
                'category': 'transfers_nip',
                'content': (
                    "Axoora processes fund transfers over dual-redundant NIBSS Instant Payment (NIP) rails:\n"
                    "• Speed: Interbank transfers settle in under 3 seconds to any commercial bank, microfinance bank, or mobile money operator in Nigeria.\n"
                    "• Personal Transfer Fee: ₦0 transfer fees forever for personal accounts.\n"
                    "• Idempotent Reconciliation: If a recipient bank experiences network downtime, our automated worker tracks the session ID proof until confirmed, preventing double-debits.\n"
                    "• Failed Transfer Reversal: Unconfirmed external bank failures are automatically credited back within minutes with instant WhatsApp receipt notification.\n"
                    "• Security Notice: Axoora staff will NEVER ask for your PIN, BVN, password, or OTP via phone call, WhatsApp, or website."
                ),
            },
            {
                'slug': 'virtual-dollar-card-guide',
                'title': 'Virtual Dollar & Naira Cards Guide for International Payments',
                'category': 'cards',
                'content': (
                    "Axoora issues instant virtual cards for domestic and cross-border transactions:\n"
                    "• Virtual Dollar Card: Built on Mastercard/Visa rails specifically for international software subscriptions (OpenAI ChatGPT, AWS, Google Cloud, Apple Music, Netflix) and foreign checkout.\n"
                    "• Acceptance: High acceptance rate with zero arbitrary monthly spend limits.\n"
                    "• Transparent Exchange: Live transparent interbank foreign exchange rates with no hidden per-transaction markup fees.\n"
                    "• Security Controls: 3D Secure OTP verification and instant 1-tap card freeze inside the mobile app or via WhatsApp chat command."
                ),
            },
            {
                'slug': 'corporate-headquarters-support-directory',
                'title': 'Axoora Corporate Headquarters, Licensing & Support Directory',
                'category': 'general',
                'content': (
                    "AXOORA Financial Technologies Limited corporate information:\n"
                    "• Regulatory License: Licensed by the Central Bank of Nigeria (CBN). Deposits insured by NDIC.\n"
                    "• Principal Headquarters: Suite 08 Block C, Cappador Mall, 85 Aguiyi Ironsi Street Maitama, Abuja, FCT, Nigeria.\n"
                    "• Official WhatsApp Desk: +234 911 000 2966 (Axoora AI & Priority Customer Desk).\n"
                    "• Official Support Email: support@axoora.ai\n"
                    "• Hours of Operation: 24/7 digital chat banking and 8:00 AM - 5:00 PM West Africa Time for physical branch consultations."
                ),
            },
        ]

        # 2. Insert Core Documents and Create Chunks
        for doc_data in core_documents:
            doc, _ = KnowledgeDocument.objects.update_or_create(
                slug=doc_data['slug'],
                defaults=doc_data,
            )

            # Chunk document by bullet points or paragraphs
            sections = [s.strip() for s in doc.content.split('\n') if s.strip() and not s.startswith('---')]
            for idx, sec in enumerate(sections):
                chunk_title = f"{doc.title} (Part {idx + 1})"
                KnowledgeChunk.objects.update_or_create(
                    source_type='document',
                    source_id=f"{doc.slug}-{idx}",
                    defaults={
                        'document': doc,
                        'chunk_title': chunk_title,
                        'content': f"{doc.title}: {sec}",
                        'keywords': f"{doc.category}, {doc.title}, {sec[:50]}",
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"✓ {len(core_documents)} Core knowledge documents chunked."))

        # 3. Ingest FAQs as RAG Knowledge Chunks
        faqs = FaqItem.objects.filter(is_active=True)
        for faq in faqs:
            KnowledgeChunk.objects.update_or_create(
                source_type='faq',
                source_id=f"faq-{faq.id}",
                defaults={
                    'chunk_title': f"FAQ: {faq.question}",
                    'content': f"Question: {faq.question}\nAnswer: {faq.answer}",
                    'keywords': f"{faq.category}, faq, {faq.question}",
                }
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {faqs.count()} FAQs indexed into RAG chunks."))

        # 4. Ingest Journal Articles as RAG Knowledge Chunks
        articles = JournalArticle.objects.filter(is_published=True)
        for art in articles:
            content_snippet = f"Title: {art.title}\nSummary: {art.summary}\nKey details: {art.content[:400]}"
            KnowledgeChunk.objects.update_or_create(
                source_type='article',
                source_id=f"art-{art.slug}",
                defaults={
                    'chunk_title': f"Journal: {art.title}",
                    'content': content_snippet,
                    'keywords': f"{art.category}, article, {art.author}, {art.title}",
                }
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {articles.count()} Journal articles indexed into RAG chunks."))

        # 5. Ingest Products as RAG Knowledge Chunks
        products = ProductItem.objects.all()
        for prod in products:
            prod_content = f"Product: {prod.name}\nCategory: {prod.get_category_display()}\nHeadline: {prod.headline}\nFee Structure: {prod.fee_structure}\nFeatures: {prod.description}"
            KnowledgeChunk.objects.update_or_create(
                source_type='product',
                source_id=f"prod-{prod.id}",
                defaults={
                    'chunk_title': f"Product: {prod.name}",
                    'content': prod_content,
                    'keywords': f"{prod.category}, product, pricing, {prod.fee_structure}, {prod.name}",
                }
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {products.count()} Products indexed into RAG chunks."))

        total_chunks = KnowledgeChunk.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✓ Total RAG chunks active in index: {total_chunks}"))
