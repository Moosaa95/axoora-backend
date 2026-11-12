import uuid
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from ..common.models import BaseModel, ActiveModelMixin, make_unique_slug
from .enums import ArticleCategory, FaqCategory, ProductCategory, ProductStatus

HERO_CONFIG_UUID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def default_onboarding_steps() -> list[dict[str, str]]:
    return [
        {
            'number': '01',
            'tag': 'INSTANT SETUP',
            'title': 'Say "Hi" on WhatsApp or Download the App',
            'description': 'Skip the bank queue entirely. Open your personal or business account in under 90 seconds directly from WhatsApp or our iOS & Android app.',
            'highlight': '90-Second KYC',
            'ctaText': 'Chat with AI Concierge',
        },
        {
            'number': '02',
            'tag': 'VERIFICATION',
            'title': 'Link Your BVN / NIN & Verify Your Store',
            'description': 'Instant automated identity and CAC verification. Unlock a dedicated Nigerian NUBAN account in your personal or registered business name.',
            'highlight': 'CBN Tier-3 Ready',
            'ctaText': 'Start Verification',
        },
        {
            'number': '03',
            'tag': 'HARDWARE & WALLET',
            'title': 'Fund Your Wallet or Request an Apex POS',
            'description': 'Start sending free personal transfers immediately, or order a Dual-SIM Apex POS terminal delivered to your shop within 24–48 hours.',
            'highlight': '48hr POS Dispatch',
            'ctaText': 'Request POS Terminal',
        },
        {
            'number': '04',
            'tag': 'LIVE SETTLEMENT',
            'title': 'Accept Payments & Settle in 0 Seconds',
            'description': 'Every card tap, bank transfer, and Paycircle contribution settles into your account instantaneously with automated WhatsApp audio & PDF receipts.',
            'highlight': 'T+0 Instant Credit',
            'ctaText': 'Explore Live Demo',
        },
    ]


class HeroConfiguration(BaseModel):
    headline_business: Any = models.CharField(
        max_length=255,
        default='Money, simplified for the street.',
    )
    subheadline_business: Any = models.TextField(
        default='One dedicated Nigerian account for your personal money, one for your store, and a dual-SIM Apex POS that settles transfers in 0 seconds.',
    )
    headline_personal: Any = models.CharField(
        max_length=255,
        default='Your AI financial concierge.',
    )
    subheadline_personal: Any = models.TextField(
        default='Bank safely on WhatsApp, split group contributions with Paycircle, and keep your savings halal with zero interest and zero hidden charges.',
    )
    announcement_ticker: Any = models.CharField(
        max_length=255,
        default='⚡ CBN Approved Dual-SIM Apex POS Batch 2 Now Dispatching Nationwide. Instant Settlement Enabled.',
    )
    announcement_active: Any = models.BooleanField(default=True)
    cta_text_primary: Any = models.CharField(max_length=100, default='Get Apex POS')
    cta_text_secondary: Any = models.CharField(max_length=100, default='Explore Features')
    trust_line: Any = models.CharField(
        max_length=255,
        default='Licensed by Central Bank of Nigeria (CBN) • Insured by NDIC • Zero Transfer Fee Personal Banking',
    )
    onboarding_steps: Any = models.JSONField(default=default_onboarding_steps, blank=True)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        verbose_name = 'Hero Configuration'
        verbose_name_plural = 'Hero Configuration'

    def __str__(self):
        return f"Hero Configuration (Updated {self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else 'New'})"

    @classmethod
    def get_or_create_config(cls):
        """Retrieve singleton hero config or initialize with deterministic UUID."""
        config = cls.objects.first()
        if not config:
            config = cls.objects.create(id=HERO_CONFIG_UUID)
        elif not config.onboarding_steps:
            config.onboarding_steps = default_onboarding_steps()
            config.save(update_fields=['onboarding_steps', 'updated_at'])
        return config

    @classmethod
    def update_config(cls, **fields):
        """Update hero config fields and persist."""
        config = cls.get_or_create_config()
        allowed = (
            'headline_business',
            'subheadline_business',
            'headline_personal',
            'subheadline_personal',
            'announcement_ticker',
            'announcement_active',
            'cta_text_primary',
            'cta_text_secondary',
            'trust_line',
            'onboarding_steps',
        )
        config.apply_updates(allowed, **fields)
        return config


class JournalArticle(BaseModel):
    slug: Any = models.SlugField(max_length=255, unique=True, db_index=True)
    category: Any = models.CharField(
        max_length=50,
        choices=ArticleCategory.choices,
        default=ArticleCategory.ENGINEERING,
    )
    title: Any = models.CharField(max_length=255)
    summary: Any = models.TextField()
    content: Any = models.TextField(blank=True, default='')
    read_time: Any = models.CharField(max_length=50, default='4 min read')
    author: Any = models.CharField(max_length=120, default='Axoora Architecture Group')
    published_date: Any = models.CharField(max_length=50, default='Oct 2026')
    is_published: Any = models.BooleanField(default=True, db_index=True)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Journal Article'
        verbose_name_plural = 'Journal Articles'

    def __str__(self):
        return f"[{self.category}] {self.title}"

    @classmethod
    def get_published(cls, category=None, search=None):
        """Retrieve published journal articles with optional category and search filters."""
        return cls.get_all(category=category, search=search, include_drafts=False)

    @classmethod
    def get_all(cls, category=None, search=None, include_drafts=False):
        """Retrieve articles with optional draft visibility, category and search filters."""
        qs = cls.objects.all() if include_drafts else cls.objects.filter(is_published=True)
        if category:
            qs = qs.filter(category__iexact=category.strip())
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search) |
                Q(author__icontains=search)
            )
        return qs

    @classmethod
    def get_by_slug(cls, slug, include_drafts=False):
        """Retrieve single article by slug."""
        try:
            qs = cls.objects.all() if include_drafts else cls.objects.filter(is_published=True)
            return qs.get(slug=slug)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_by_id_or_slug(cls, identifier, include_drafts=True):
        """Retrieve single article by UUID or slug."""
        qs = cls.objects.all() if include_drafts else cls.objects.filter(is_published=True)
        try:
            return qs.get(id=identifier)
        except (cls.DoesNotExist, ValueError, TypeError, ValidationError):
            return qs.filter(slug=identifier).first()

    @classmethod
    def create_article(
        cls,
        title,
        summary,
        category=ArticleCategory.ENGINEERING,
        content='',
        author='Axoora Editorial Board',
        read_time='4 min read',
        published_date='Oct 2026',
        is_published=True,
        slug=None,
    ):
        """Create and persist a new journal/news article."""
        clean_title = title.strip()
        target_slug = make_unique_slug(cls, slug or clean_title, fallback='article')

        return cls.objects.create(
            title=clean_title,
            slug=target_slug,
            category=category,
            summary=summary.strip(),
            content=content.strip(),
            author=author.strip(),
            read_time=read_time.strip(),
            published_date=published_date.strip(),
            is_published=is_published,
        )

    @classmethod
    def update_article(cls, identifier, **fields):
        """Update existing article fields."""
        article = cls.get_by_id_or_slug(identifier, include_drafts=True)
        if not article and fields.get('title'):
            article = cls.objects.filter(title__iexact=fields['title'].strip()).first()
        if not article:
            if fields.get('title') and fields.get('summary'):
                return cls.create_article(slug=identifier, **fields)
            return None

        allowed = ('title', 'category', 'summary', 'content', 'author', 'read_time', 'published_date', 'is_published')
        article.apply_updates(allowed, **fields)
        return article

    @classmethod
    def delete_article(cls, identifier):
        """Delete article by UUID or slug."""
        article = cls.get_by_id_or_slug(identifier, include_drafts=True)
        if not article:
            return False
        article.delete()
        return True


class FaqItem(BaseModel, ActiveModelMixin):
    question: Any = models.CharField(max_length=300)
    answer: Any = models.TextField()
    category: Any = models.CharField(
        max_length=50,
        choices=FaqCategory.choices,
        default=FaqCategory.GENERAL,
    )
    order: Any = models.PositiveIntegerField(default=0)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta, ActiveModelMixin.Meta):
        ordering = ['order', 'created_at']
        verbose_name = 'FAQ Item'
        verbose_name_plural = 'FAQ Items'

    def __str__(self):
        return f"[{self.category}] {self.question}"

    @classmethod
    def get_active_faqs(cls, category=None, search=None, include_inactive=False):
        """Retrieve active FAQ items with optional filters."""
        qs = cls.objects.all() if include_inactive else cls.objects.filter(is_active=True)
        if category and category.lower() != 'all':
            qs = qs.filter(category__iexact=category.strip())
        if search:
            qs = qs.filter(
                Q(question__icontains=search) |
                Q(answer__icontains=search)
            )
        return qs.order_by('order', 'created_at')

    @classmethod
    def get_by_id(cls, faq_id):
        """Retrieve single FAQ item by UUID."""
        try:
            return cls.objects.get(id=faq_id)
        except (cls.DoesNotExist, ValueError, TypeError):
            return None

    @classmethod
    def create_faq(cls, question, answer, category=FaqCategory.GENERAL, order=0, is_active=True):
        """Create and persist a new FAQ entry."""
        return cls.objects.create(
            question=question.strip(),
            answer=answer.strip(),
            category=category,
            order=order,
            is_active=is_active,
        )

    @classmethod
    def update_faq(cls, faq_id, **fields):
        """Update existing FAQ fields."""
        item = cls.get_by_id(faq_id)
        if not item:
            return None
        allowed = ('question', 'answer', 'category', 'order', 'is_active')
        item.apply_updates(allowed, **fields)
        return item

    @classmethod
    def delete_faq(cls, faq_id):
        """Delete an FAQ item."""
        item = cls.get_by_id(faq_id)
        if not item:
            return False
        item.delete()
        return True


class MerchantStory(BaseModel):
    name: Any = models.CharField(max_length=120)
    role: Any = models.CharField(max_length=120)
    location: Any = models.CharField(max_length=120)
    quote: Any = models.TextField()
    stat_label: Any = models.CharField(max_length=100)
    stat_value: Any = models.CharField(max_length=50)
    badge: Any = models.CharField(max_length=100, default='Verified Merchant')
    accent_color: Any = models.CharField(max_length=20, default='#10B981')
    image_url: Any = models.CharField(max_length=500, blank=True, default='')
    featured: Any = models.BooleanField(default=False, db_index=True)
    order: Any = models.PositiveIntegerField(default=0)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['order', '-created_at']
        verbose_name = 'Merchant Story'
        verbose_name_plural = 'Merchant Stories'

    def __str__(self):
        return f"{self.name} - {self.role} ({self.location})"

    @classmethod
    def get_all(cls, featured_only=False):
        """Retrieve customer stories."""
        qs = cls.objects.all()
        if featured_only:
            qs = qs.filter(featured=True)
        return qs.order_by('order', '-created_at')

    @classmethod
    def create_story(cls, **fields):
        """Create and persist a merchant story."""
        return cls.objects.create(
            name=fields.get('name', '').strip(),
            role=fields.get('role', '').strip(),
            location=fields.get('location', '').strip(),
            quote=fields.get('quote', '').strip(),
            stat_label=fields.get('stat_label', 'Weekly Turnover').strip(),
            stat_value=fields.get('stat_value', '₦5M+').strip(),
            badge=fields.get('badge', 'Verified Merchant').strip(),
            accent_color=fields.get('accent_color', '#00DF8F').strip(),
            image_url=fields.get('image_url', '/merchants/bilkisu.jpg').strip(),
            featured=fields.get('featured', True),
            order=fields.get('order', 0),
        )

    @classmethod
    def update_story(cls, story_id, **fields):
        """Update an existing merchant story by UUID or fallback name match / upsert."""
        story = cls.get_by_id(story_id)
        if not story and fields.get('name'):
            story = cls.objects.filter(name__iexact=str(fields['name']).strip()).first()
        if not story:
            if fields.get('name') and fields.get('quote'):
                return cls.create_story(**fields)
            return None

        allowed = (
            'name', 'role', 'location', 'quote', 'stat_label', 'stat_value',
            'badge', 'accent_color', 'image_url', 'featured', 'order',
        )
        story.apply_updates(allowed, **fields)
        return story

    @classmethod
    def delete_story(cls, story_id):
        """Delete a merchant story by UUID or name."""
        if cls.delete_by_id(story_id):
            return True
        story = cls.objects.filter(name__iexact=str(story_id).strip()).first()
        if story:
            story.delete()
            return True
        return False


class ProductItem(BaseModel):
    name: Any = models.CharField(max_length=120)
    category: Any = models.CharField(
        max_length=30,
        choices=ProductCategory.choices,
        default=ProductCategory.PERSONAL,
    )
    headline: Any = models.CharField(max_length=255)
    fee_structure: Any = models.CharField(max_length=120)
    status: Any = models.CharField(
        max_length=30,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )
    highlight: Any = models.CharField(max_length=120)
    description: Any = models.TextField()
    order: Any = models.PositiveIntegerField(default=0)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['order', 'created_at']
        verbose_name = 'Product Item'
        verbose_name_plural = 'Product Items'

    def __str__(self):
        return f"{self.name} ({self.category})"

    @classmethod
    def get_all(cls, category=None, status=None):
        """Retrieve catalog products."""
        qs = cls.objects.all()
        if category:
            qs = qs.filter(category=category)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('order', 'created_at')

    @classmethod
    def create_product(cls, **fields):
        """Create and persist a product item."""
        return cls.objects.create(
            name=fields.get('name', '').strip(),
            category=fields.get('category', ProductCategory.PERSONAL),
            headline=fields.get('headline', '').strip(),
            fee_structure=fields.get('fee_structure', '₦0 Fee').strip(),
            status=fields.get('status', ProductStatus.ACTIVE),
            highlight=fields.get('highlight', '').strip(),
            description=fields.get('description', '').strip(),
            order=fields.get('order', 0),
        )

    @classmethod
    def update_product(cls, product_id, **fields):
        """Update an existing product item by UUID or fallback name match / upsert."""
        product = cls.get_by_id(product_id)
        if not product and fields.get('name'):
            product = cls.objects.filter(name__iexact=str(fields['name']).strip()).first()
        if not product:
            if fields.get('name') and fields.get('headline'):
                return cls.create_product(**fields)
            return None

        allowed = ('name', 'category', 'headline', 'fee_structure', 'status', 'highlight', 'description', 'order')
        product.apply_updates(allowed, **fields)
        return product

    @classmethod
    def delete_product(cls, product_id):
        """Delete a product item by UUID or name."""
        if cls.delete_by_id(product_id):
            return True
        product = cls.objects.filter(name__iexact=str(product_id).strip()).first()
        if product:
            product.delete()
            return True
        return False
