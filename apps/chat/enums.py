from django.db import models


class ChatStatus(models.TextChoices):
    AI_ACTIVE = 'ai_active', 'AI Concierge Active'
    ESCALATED = 'escalated', 'Escalated to Human Agent'
    HUMAN_ACTIVE = 'human_active', 'Human Agent Active'
    RESOLVED = 'resolved', 'Resolved'
    CLOSED = 'closed', 'Closed'


class MessageSender(models.TextChoices):
    USER = 'user', 'Customer'
    AI = 'ai', 'Axoora AI Assistant'
    AGENT = 'agent', 'Human Agent'
    SYSTEM = 'system', 'System'


class KnowledgeCategory(models.TextChoices):
    FAQ = 'faq', 'Frequently Asked Questions'
    POS_HARDWARE = 'pos_hardware', 'Apex POS Terminal Manual'
    ISLAMIC_BANKING = 'islamic_banking', 'Non-Interest Islamic Banking'
    TRANSFERS_NIP = 'transfers_nip', 'NIBSS Rails & Instant Transfers'
    ACCOUNTS_FEES = 'accounts_fees', 'Accounts, Shop NUBAN & Fees'
    CARDS = 'cards', 'Virtual Naira & Dollar Cards'
    SECURITY = 'security', 'Security & Fraud Prevention'
    POLICIES = 'policies', 'Bank Policies & Terms'
    GENERAL = 'general', 'General Corporate Overview'
