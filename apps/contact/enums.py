from django.db import models


class InquiryCategory(models.TextChoices):
    GENERAL = 'general', 'General Inquiry'
    POS = 'pos', 'POS Terminal & Agency'
    BUSINESS = 'business', 'Corporate & Merchant Banking'
    PARTNERSHIP = 'partnership', 'Strategic Partnership'
    SECURITY = 'security', 'Security & Whistleblowing'


class InquiryStatus(models.TextChoices):
    NEW = 'new', 'New'
    IN_REVIEW = 'in_review', 'In Review'
    RESOLVED = 'resolved', 'Resolved'
    ARCHIVED = 'archived', 'Archived'
