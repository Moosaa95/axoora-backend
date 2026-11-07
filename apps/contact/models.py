from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from ..common.models import BaseModel
from .enums import InquiryCategory, InquiryStatus


class ContactInquiry(BaseModel):
    full_name: Any = models.CharField(max_length=255)
    email: Any = models.EmailField()
    phone: Any = models.CharField(max_length=50, blank=True, default='')
    category: Any = models.CharField(
        max_length=30,
        choices=InquiryCategory.choices,
        default=InquiryCategory.GENERAL,
    )
    subject: Any = models.CharField(max_length=255)
    message: Any = models.TextField()
    status: Any = models.CharField(
        max_length=20,
        choices=InquiryStatus.choices,
        default=InquiryStatus.NEW,
    )
    response_notes: Any = models.TextField(blank=True, default='')
    ip_address: Any = models.GenericIPAddressField(null=True, blank=True)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['-created_at']
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f"[{self.category}] {self.subject} - {self.full_name}"

    # =========================================================================
    # Model Classmethods for queries
    # =========================================================================

    @classmethod
    def get_all(cls, status=None, category=None, search=None):
        """Retrieve all contact inquiries with optional filtering."""
        qs = cls.objects.all()
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(subject__icontains=search) |
                Q(message__icontains=search)
            )
        return qs

    @classmethod
    def create_inquiry(
        cls,
        full_name,
        email,
        subject,
        message,
        phone='',
        category=InquiryCategory.GENERAL,
        ip_address=None,
    ):
        """Create and persist a new contact message."""
        return cls.objects.create(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
            category=category,
            subject=subject.strip(),
            message=message.strip(),
            ip_address=ip_address,
            status=InquiryStatus.NEW,
        )

    @classmethod
    def update_status(cls, inquiry_id, new_status, response_notes=None):
        """Update inquiry lifecycle status."""
        inquiry = cls.get_by_id(inquiry_id)
        if not inquiry:
            return None
        inquiry.status = new_status
        if response_notes is not None:
            inquiry.response_notes = response_notes
        inquiry.save(update_fields=['status', 'response_notes', 'updated_at'])
        return inquiry
