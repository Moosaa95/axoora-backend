from typing import Any
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.team.models import Role, TeamMember
from apps.team.enums import MemberStatus, Department


class Command(BaseCommand):
    help = 'Seeds initial built-in roles and connects the primary admin superuser to Super Admin role.'

    def handle(self, *args, **options):
        self.stdout.write("Initializing Axoora roles and team configuration...")

        roles_config = [
            {
                'name': 'Super Admin',
                'slug': 'super-admin',
                'description': 'Full administrative control with unrestricted permissions across all modules.',
                'permissions': ['*'],
                'is_system': True,
            },
            {
                'name': 'Operations Lead',
                'slug': 'operations-lead',
                'description': 'Manage merchant onboarding leads, review KYC, and dispatch POS terminals.',
                'permissions': [
                    'leads.view',
                    'leads.manage',
                    'pos.dispatch',
                    'inquiries.view',
                    'inquiries.manage',
                ],
                'is_system': True,
            },
            {
                'name': 'Content & Editorial Manager',
                'slug': 'content-editorial-manager',
                'description': 'Author and publish journal articles, news updates, and press releases.',
                'permissions': [
                    'content.view',
                    'content.manage',
                ],
                'is_system': True,
            },
            {
                'name': 'Customer Concierge Specialist',
                'slug': 'customer-concierge-specialist',
                'description': 'Handle live customer support chats, resolve inquiries, and manage FAQs.',
                'permissions': [
                    'inquiries.view',
                    'inquiries.manage',
                    'chat.view',
                    'chat.manage',
                    'knowledge.manage',
                ],
                'is_system': True,
            },
            {
                'name': 'Compliance & Audit Officer',
                'slug': 'compliance-audit-officer',
                'description': 'Read-only audit visibility across leads, inquiries, team, and regulatory logs.',
                'permissions': [
                    'leads.view',
                    'content.view',
                    'inquiries.view',
                    'chat.view',
                    'team.view',
                ],
                'is_system': True,
            },
        ]

        created_count = 0
        for item in roles_config:
            role, created = Role.objects.get_or_create(
                slug=item['slug'],
                defaults={
                    'name': item['name'],
                    'description': item['description'],
                    'permissions': item['permissions'],
                    'is_system': item['is_system'],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Role '{role.name}' created."))

        # Link superuser to Super Admin
        User: Any = get_user_model()
        admin_user: Any = User.objects.filter(is_superuser=True).first()
        super_admin_role = Role.objects.filter(slug='super-admin').first()

        if admin_user and super_admin_role:
            member, m_created = TeamMember.objects.get_or_create(
                user=admin_user,
                defaults={
                    'role': super_admin_role,
                    'job_title': 'Chief Technology & Operations Officer',
                    'department': Department.EXECUTIVE,
                    'status': MemberStatus.ACTIVE,
                },
            )
            if m_created or member.role != super_admin_role:
                member.role = super_admin_role
                member.save()
                self.stdout.write(self.style.SUCCESS(f"✓ Connected superuser '{admin_user.username}' to 'Super Admin' role."))

        self.stdout.write(self.style.SUCCESS("✓ Role and team initialization completed."))
