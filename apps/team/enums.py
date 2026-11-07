from django.db import models


class MemberStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    INVITED = 'invited', 'Invited'
    SUSPENDED = 'suspended', 'Suspended'


class Department(models.TextChoices):
    OPERATIONS = 'Operations', 'Operations & POS Logistics'
    OPERATIONS_LOWER = 'operations', 'Operations'
    SUPPORT = 'Support', 'Customer Support & Concierge'
    CUSTOMER_SUPPORT_LOWER = 'customer_support', 'Customer Support'
    EDITORIAL = 'Editorial', 'Content, News & Growth'
    MARKETING_LOWER = 'marketing', 'Marketing'
    EXECUTIVE = 'Executive', 'Executive Management'
    EXECUTIVE_LOWER = 'executive', 'Executive'
    ENGINEERING = 'Engineering', 'Engineering & Platform'
    ENGINEERING_LOWER = 'engineering', 'Engineering'
    COMPLIANCE = 'compliance', 'Compliance'
    FINANCE = 'finance', 'Finance'


# System Permissions Registry (Structured RBAC without Maker-Checker)
SYSTEM_PERMISSIONS = [
    # Leads & POS Logistics
    {
        'id': 'leads.view',
        'name': 'View Leads & Applications',
        'category': 'Leads & POS',
        'description': 'View onboarding submissions, business applications, and contact info',
    },
    {
        'id': 'leads.manage',
        'name': 'Manage Lead Pipeline',
        'category': 'Leads & POS',
        'description': 'Update lead status, qualification, notes, and export CSV reports',
    },
    {
        'id': 'pos.dispatch',
        'name': 'POS Terminal Logistics',
        'category': 'Leads & POS',
        'description': 'Assign POS terminal serials, update dispatch status, and manage shipping codes',
    },

    # Content, Blog & News
    {
        'id': 'content.view',
        'name': 'View Content Catalog',
        'category': 'Content & Blog',
        'description': 'Read journal articles, news stories, press releases, and FAQs',
    },
    {
        'id': 'content.manage',
        'name': 'Publish & Edit Articles & News',
        'category': 'Content & Blog',
        'description': 'Create, edit, publish, and delete blog articles, press releases, and news items',
    },

    # Customer Inquiries & Contact
    {
        'id': 'inquiries.view',
        'name': 'View Customer Inquiries',
        'category': 'Inquiries & Contact',
        'description': 'Inspect incoming partnership, institutional, and support messages',
    },
    {
        'id': 'inquiries.manage',
        'name': 'Resolve Customer Inquiries',
        'category': 'Inquiries & Contact',
        'description': 'Reply to inquiries, add internal audit notes, and mark as resolved',
    },

    # Live Chat & AI Concierge
    {
        'id': 'chat.view',
        'name': 'View Live Chat Sessions',
        'category': 'Live Support',
        'description': 'Monitor AI conversational banking sessions and human escalation requests',
    },
    {
        'id': 'chat.manage',
        'name': 'Agent Live Chat Takeover',
        'category': 'Live Support',
        'description': 'Respond to customer support tickets in real-time and resolve sessions',
    },
    {
        'id': 'knowledge.manage',
        'name': 'Manage Knowledge Base',
        'category': 'Live Support',
        'description': 'Add and update AI RAG chunks, compliance FAQs, and automated response rules',
    },

    # Team & Access Control
    {
        'id': 'team.view',
        'name': 'View Team Directory',
        'category': 'Team & Access',
        'description': 'View team member roster, roles, and assigned access privileges',
    },
    {
        'id': 'team.manage',
        'name': 'Manage Team Members',
        'category': 'Team & Access',
        'description': 'Add team members, edit job profiles, and toggle active/suspended status',
    },
    {
        'id': 'roles.manage',
        'name': 'Create & Edit Custom Roles',
        'category': 'Team & Access',
        'description': 'Create new roles, modify granular permissions, and assign them directly',
    },

    # System & Settings
    {
        'id': 'system.settings',
        'name': 'System & Compliance Settings',
        'category': 'System',
        'description': 'Configure regulatory licenses, CBN hotlines, and security credentials',
    },
]

ALL_PERMISSION_IDS = [p['id'] for p in SYSTEM_PERMISSIONS]
