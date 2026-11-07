from django.db import models


class WaitlistInterest(models.TextChoices):
    PERSONAL = 'personal', 'Personal Banking'
    BUSINESS = 'business', 'Business Account'
    POS_AGENT = 'pos-agent', 'POS Terminal & Agent'
    AGGREGATOR = 'aggregator', 'Aggregator Network'


class WaitlistStatus(models.TextChoices):
    NEW = 'new', 'New Lead'
    CONTACTED = 'contacted', 'Contacted'
    APPROVED = 'approved', 'Approved'
    DISPATCHED = 'dispatched', 'Terminal Dispatched'
    ARCHIVED = 'archived', 'Archived'
