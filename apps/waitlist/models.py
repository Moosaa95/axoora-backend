from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from ..common.models import BaseModel, UUIDReferenceModel
from .enums import WaitlistInterest, WaitlistStatus


class WaitlistLead(BaseModel, UUIDReferenceModel):
    full_name: Any = models.CharField(max_length=255)
    whatsapp_number: Any = models.CharField(max_length=50)
    email: Any = models.EmailField()
    city: Any = models.CharField(max_length=120, blank=True, default='')
    state: Any = models.CharField(max_length=120, blank=True, default='')
    business_name: Any = models.CharField(max_length=255, blank=True, default='')
    interest: Any = models.CharField(
        max_length=30,
        choices=WaitlistInterest.choices,
        default=WaitlistInterest.BUSINESS,
    )
    consent: Any = models.BooleanField(default=True)
    status: Any = models.CharField(
        max_length=20,
        choices=WaitlistStatus.choices,
        default=WaitlistStatus.NEW,
    )
    notes: Any = models.TextField(blank=True, default='')
    source: Any = models.CharField(max_length=100, blank=True, default='website')
    ip_address: Any = models.GenericIPAddressField(null=True, blank=True)
    user_agent: Any = models.TextField(blank=True, default='')

    business_type: Any = models.CharField(max_length=50, blank=True, default='')  # ltd, bn, unregistered
    cac_number: Any = models.CharField(max_length=100, blank=True, default='')
    sector: Any = models.CharField(max_length=100, blank=True, default='')
    pos_model: Any = models.CharField(max_length=100, blank=True, default='')  # ax-smart, ax-mini, ax-audio
    terminal_count: Any = models.PositiveIntegerField(default=1)
    street_address: Any = models.TextField(blank=True, default='')
    settlement_type: Any = models.CharField(max_length=50, blank=True, default='instant')
    settlement_bank: Any = models.CharField(max_length=120, blank=True, default='')
    settlement_account_number: Any = models.CharField(max_length=50, blank=True, default='')
    settlement_account_name: Any = models.CharField(max_length=255, blank=True, default='')
    application_ref: Any = models.CharField(max_length=50, blank=True, default='', db_index=True)
    tracking_number: Any = models.CharField(max_length=50, blank=True, default='', db_index=True)
    metadata: Any = models.JSONField(default=dict, blank=True)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta, UUIDReferenceModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Waitlist Submission'
        verbose_name_plural = 'Waitlist Submissions'


    def __str__(self):
        ref_label = f" [{self.application_ref}]" if self.application_ref else ""
        return f"{self.full_name}{ref_label} ({self.interest}) - {self.whatsapp_number}"

    # =========================================================================
    # Model Classmethods for queries (Encapsulating data access)
    # =========================================================================

    @classmethod
    def get_all(cls, status=None, interest=None, search=None):
        """Retrieve all waitlist leads with optional filtering and search."""
        qs = cls.objects.all()
        if status:
            qs = qs.filter(status=status)
        if interest:
            qs = qs.filter(interest=interest)
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(whatsapp_number__icontains=search) |
                Q(city__icontains=search) |
                Q(business_name__icontains=search) |
                Q(application_ref__icontains=search) |
                Q(tracking_number__icontains=search) |
                Q(cac_number__icontains=search)
            )
        return qs

    @classmethod
    def get_by_reference_id(cls, reference_id):
        """Retrieve single lead by UUID reference or None."""
        try:
            return cls.objects.get(reference_id=reference_id)
        except (cls.DoesNotExist, ValueError, TypeError, ValidationError):
            return None

    @classmethod
    def get_by_ref_or_tracking(cls, query):
        """Retrieve single lead by application_ref, tracking_number, or reference_id string."""
        clean = (query or '').strip()
        if not clean:
            return None
        return cls.objects.filter(
            Q(application_ref__iexact=clean) |
            Q(tracking_number__iexact=clean)
        ).first()

    @classmethod
    def create_lead(
        cls,
        full_name,
        whatsapp_number,
        email,
        city='',
        state='',
        business_name='',
        interest=WaitlistInterest.BUSINESS,
        consent=True,
        source='website',
        ip_address=None,
        user_agent='',
        notes='',
        business_type='',
        cac_number='',
        sector='',
        pos_model='',
        terminal_count=1,
        street_address='',
        settlement_type='instant',
        settlement_bank='',
        settlement_account_number='',
        settlement_account_name='',
        application_ref='',
        tracking_number='',
        metadata=None,
    ):
        """Create and persist a new waitlist lead or business onboarding application."""
        return cls.objects.create(
            full_name=full_name.strip(),
            whatsapp_number=whatsapp_number.strip(),
            email=email.strip().lower(),
            city=city.strip(),
            state=state.strip(),
            business_name=business_name.strip(),
            interest=interest,
            consent=consent,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            notes=notes,
            business_type=business_type.strip(),
            cac_number=cac_number.strip(),
            sector=sector.strip(),
            pos_model=pos_model.strip(),
            terminal_count=max(1, int(terminal_count or 1)),
            street_address=street_address.strip(),
            settlement_type=settlement_type.strip(),
            settlement_bank=settlement_bank.strip(),
            settlement_account_number=settlement_account_number.strip(),
            settlement_account_name=settlement_account_name.strip(),
            application_ref=application_ref.strip(),
            tracking_number=tracking_number.strip(),
            metadata=metadata or {},
            status=WaitlistStatus.NEW,
        )


    @classmethod
    def update_lead_status(cls, lead_id, new_status, notes=None):
        """Update the lifecycle status of a lead."""
        lead = cls.get_by_id(lead_id)
        if not lead:
            return None
        lead.status = new_status
        if notes is not None:
            lead.notes = notes
        lead.save(update_fields=['status', 'notes', 'updated_at'])
        return lead

    @classmethod
    def delete_by_id(cls, lead_id):
        """Delete lead by ID. Returns boolean success."""
        lead = cls.get_by_id(lead_id)
        if lead:
            lead.delete()
            return True
        return False
