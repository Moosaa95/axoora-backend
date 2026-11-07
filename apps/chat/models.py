from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..common.models import BaseModel, ActiveModelMixin
from .enums import ChatStatus, MessageSender, KnowledgeCategory

User: Any = get_user_model()


class ChatSession(BaseModel):
    customer_name: Any = models.CharField(max_length=255, blank=True, default='')
    customer_phone: Any = models.CharField(max_length=50, blank=True, default='')
    customer_email: Any = models.EmailField(blank=True, default='')
    status: Any = models.CharField(
        max_length=30,
        choices=ChatStatus.choices,
        default=ChatStatus.AI_ACTIVE,
        db_index=True,
    )
    issue_summary: Any = models.CharField(max_length=255, blank=True, default='')
    escalation_reason: Any = models.TextField(blank=True, default='')
    escalated_at: Any = models.DateTimeField(null=True, blank=True)
    resolved_at: Any = models.DateTimeField(null=True, blank=True)
    assigned_agent: Any = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_chats')
    ip_address: Any = models.GenericIPAddressField(null=True, blank=True)
    user_agent: Any = models.TextField(blank=True, default='')

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self):
        name = self.customer_name or f"Guest-{str(self.id)[:8]}"
        return f"[{self.get_status_display()}] {name} ({self.created_at.strftime('%b %d, %H:%M')})"

    @property
    def session_id(self):
        """Unified session UUID identifier matching primary key."""
        return self.id

    @property
    def ticket_code(self):
        return f"AX-{str(self.id)[:8].upper()}"

    # =========================================================================
    # Model Classmethods for queries
    # =========================================================================

    @classmethod
    def _base_queryset(cls):
        """Return ChatSession queryset with assigned_agent joined and messages prefetched."""
        return cls.objects.select_related('assigned_agent').prefetch_related('messages')

    @classmethod
    def get_or_create_session(cls, session_id=None, customer_name='', customer_phone='', ip_address=None, user_agent=''):
        """Retrieve existing chat session or create a new one."""
        session = cls.get_by_session_id(session_id) if session_id else None

        if not session:
            session = cls.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else '',
            )
        else:
            dirty = False
            if customer_name and not session.customer_name:
                session.customer_name = customer_name
                dirty = True
            if customer_phone and not session.customer_phone:
                session.customer_phone = customer_phone
                dirty = True
            if ip_address and not session.ip_address:
                session.ip_address = ip_address
                dirty = True
            if dirty:
                session.save()

        return session

    @classmethod
    def get_by_session_id(cls, session_id):
        """Retrieve single session by UUID or None (delegates to BaseModel.get_by_id)."""
        return cls.get_by_id(session_id)

    @classmethod
    def get_all_sessions(cls, status=None, search=None):
        """Retrieve chat sessions with optional status and search filters."""
        qs = cls._base_queryset().all()
        if status and status != 'all':
            qs = qs.filter(status=status)
        if search:
            clean = search.strip()
            qs = qs.filter(
                Q(customer_name__icontains=clean) |
                Q(customer_phone__icontains=clean) |
                Q(customer_email__icontains=clean) |
                Q(issue_summary__icontains=clean) |
                Q(escalation_reason__icontains=clean)
            )
        return qs.order_by('-updated_at')

    @classmethod
    def update_session(cls, session_id, **fields):
        """Update session status or customer metadata."""
        session = cls.get_by_session_id(session_id)
        if not session:
            return None
        if fields.get('status') == ChatStatus.RESOLVED and not session.resolved_at:
            fields['resolved_at'] = timezone.now()
        allowed = ('status', 'customer_name', 'customer_phone', 'customer_email', 'issue_summary', 'escalation_reason', 'resolved_at')
        session.apply_updates(allowed, **fields)
        return session

    @classmethod
    def escalate_session(cls, session_id, customer_name, customer_phone, customer_email='', reason=''):
        """Escalate a session from AI to human agent."""
        session = cls.get_by_session_id(session_id)
        if not session:
            return None
        session.customer_name = customer_name
        session.customer_phone = customer_phone
        if customer_email:
            session.customer_email = customer_email
        if reason:
            session.escalation_reason = reason
        session.status = ChatStatus.ESCALATED
        session.escalated_at = timezone.now()
        session.save()
        return session


class ChatMessage(BaseModel):
    session: Any = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender: Any = models.CharField(
        max_length=20,
        choices=MessageSender.choices,
        default=MessageSender.USER,
    )
    text: Any = models.TextField()
    suggested_actions: Any = models.JSONField(default=list, blank=True)
    is_escalation_trigger: Any = models.BooleanField(default=False)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"[{self.sender.upper()}] {self.text[:50]}"

    @classmethod
    def create_message(cls, session, sender, text, suggested_actions=None, is_escalation_trigger=False):
        """Record a chat message in the transcript."""
        return cls.objects.create(
            session=session,
            sender=sender,
            text=text,
            suggested_actions=suggested_actions or [],
            is_escalation_trigger=is_escalation_trigger,
        )


class ChatKnowledgeRule(BaseModel, ActiveModelMixin):
    title: Any = models.CharField(max_length=200)
    keywords: Any = models.TextField(help_text="Comma-separated keywords or regex expressions that trigger this rule")
    response_text: Any = models.TextField(help_text="The AI answer provided to the customer")
    suggested_actions: Any = models.JSONField(default=list, blank=True, help_text="List of quick suggestion buttons")
    priority: Any = models.IntegerField(default=0, help_text="Higher priority rules match first")

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta, ActiveModelMixin.Meta):
        ordering = ['-priority', 'created_at']
        verbose_name = 'Chat Knowledge Rule'
        verbose_name_plural = 'Chat Knowledge Rules'

    def __str__(self):
        return self.title

    @classmethod
    def get_active_rules(cls):
        return cls.objects.filter(is_active=True).order_by('-priority')


class KnowledgeDocument(BaseModel, ActiveModelMixin):
    title: Any = models.CharField(max_length=255)
    slug: Any = models.SlugField(max_length=255, unique=True, db_index=True)
    category: Any = models.CharField(
        max_length=50,
        choices=KnowledgeCategory.choices,
        default=KnowledgeCategory.GENERAL,
    )
    content: Any = models.TextField(help_text="Detailed knowledge content in Markdown or Plain Text")
    source_url: Any = models.CharField(max_length=255, blank=True, default='')

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta, ActiveModelMixin.Meta):
        ordering = ['category', 'title']
        verbose_name = 'RAG Knowledge Document'
        verbose_name_plural = 'RAG Knowledge Documents'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    @classmethod
    def get_all_active(cls, category=None):
        qs = cls.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        return qs

    @classmethod
    def get_by_slug(cls, slug):
        try:
            return cls.objects.get(slug=slug, is_active=True)
        except cls.DoesNotExist:
            return None


class KnowledgeChunk(BaseModel):
    document: Any = models.ForeignKey(
        KnowledgeDocument,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    chunk_title: Any = models.CharField(max_length=255)
    content: Any = models.TextField(help_text="Chunk text for retrieval")
    keywords: Any = models.TextField(blank=True, default='', help_text="Tokens and tags for lexical indexing")
    embedding: Any = models.JSONField(null=True, blank=True, help_text="Optional vector embedding list of floats")
    source_type: Any = models.CharField(max_length=50, default='document')
    source_id: Any = models.CharField(max_length=100, blank=True, default='')

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['chunk_title']
        verbose_name = 'RAG Knowledge Chunk'
        verbose_name_plural = 'RAG Knowledge Chunks'

    def __str__(self):
        return f"{self.chunk_title} ({len(self.content)} chars)"

    @classmethod
    def get_all_chunks(cls):
        return cls.objects.all().select_related('document')
