import re
from typing import Any
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Prefetch, Q
from django.conf import settings
from django.contrib.auth import get_user_model
from ..common.models import BaseModel, make_unique_slug
from .enums import MemberStatus, Department, ALL_PERMISSION_IDS


class Role(BaseModel):
    name: Any = models.CharField(max_length=120, unique=True)
    slug: Any = models.SlugField(max_length=120, unique=True, db_index=True)
    description: Any = models.TextField(blank=True, default='')
    permissions: Any = models.JSONField(default=list, blank=True)  # List of permission ID strings
    is_system: Any = models.BooleanField(default=False)  # If True, cannot be deleted (e.g. Super Admin)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['-is_system', 'name']
        verbose_name = 'Role & Permission Set'
        verbose_name_plural = 'Roles & Permission Sets'

    def __str__(self):
        return self.name

    @property
    def member_count(self) -> int:
        annotated = getattr(self, '_member_count', None)
        if annotated is not None:
            return int(annotated)
        return self.members.count()

    # =========================================================================
    # Model Classmethods for queries (Encapsulating data access)
    # =========================================================================

    @classmethod
    def _base_queryset(cls):
        """Return Role queryset pre-annotated with member count to prevent N+1 queries."""
        return cls.objects.annotate(_member_count=Count('members'))

    @classmethod
    def get_all(cls):
        """Retrieve all defined roles with annotated member counts in a single query."""
        return cls._base_queryset().order_by('-is_system', 'name')

    @classmethod
    def get_by_slug(cls, slug):
        """Retrieve single role by slug or None."""
        try:
            return cls._base_queryset().get(slug=slug)
        except cls.DoesNotExist:
            return None

    @classmethod
    def create_role(cls, name, description='', permissions=None):
        """Create and persist a new custom role."""
        clean_name = name.strip()
        slug = make_unique_slug(cls, clean_name, fallback='role')
        perms = permissions if isinstance(permissions, list) else []
        role = cls.objects.create(
            name=clean_name,
            slug=slug,
            description=description.strip(),
            permissions=perms,
            is_system=False,
        )
        role._member_count = 0
        return role

    @classmethod
    def update_role(cls, role_id, name=None, description=None, permissions=None):
        """Update an existing custom role."""
        role = cls.get_by_id(role_id)
        if not role:
            return None

        update_fields = ['updated_at']
        if name and not role.is_system:
            role.name = name.strip()
            update_fields.append('name')
        if description is not None:
            role.description = description.strip()
            update_fields.append('description')
        if permissions is not None:
            role.permissions = permissions if isinstance(permissions, list) else []
            update_fields.append('permissions')

        role.save(update_fields=update_fields)
        return role

    @classmethod
    def delete_role(cls, role_id):
        """Delete a role if not a system role."""
        role = cls.get_by_id(role_id)
        if not role or role.is_system:
            return False
        role.delete()
        return True


class TeamMember(BaseModel):
    user: Any = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_profile',
    )
    role: Any = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    job_title: Any = models.CharField(max_length=120, blank=True, default='')
    phone_number: Any = models.CharField(max_length=50, blank=True, default='')
    department: Any = models.CharField(
        max_length=80,
        choices=Department.choices,
        default=Department.OPERATIONS,
    )
    status: Any = models.CharField(
        max_length=20,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE,
    )
    custom_permissions: Any = models.JSONField(default=list, blank=True)

    objects: Any = models.Manager()

    class Meta(BaseModel.Meta):
        ordering = ['user__first_name', 'user__last_name', '-created_at']
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        name = self.full_name or self.user.username
        role_label = f" ({self.role.name})" if self.role else ""
        return f"{name}{role_label}"

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full or self.user.username

    def get_effective_permissions(self):
        """Return the complete resolved list of permission codes granted to this member."""
        if self.user.is_superuser or (self.role and '*' in self.role.permissions):
            return list(ALL_PERMISSION_IDS) + ['*']

        perms = set()
        if self.role and isinstance(self.role.permissions, list):
            perms.update(self.role.permissions)
        if isinstance(self.custom_permissions, list):
            perms.update(self.custom_permissions)
        return list(perms)

    def has_perm(self, perm_code):
        """Check if this team member is granted a specific permission."""
        if self.status != MemberStatus.ACTIVE:
            return False
        effective = self.get_effective_permissions()
        return '*' in effective or perm_code in effective

    # =========================================================================
    # Model Classmethods for queries
    # =========================================================================

    @classmethod
    def _base_queryset(cls):
        """
        Return TeamMember queryset with user joined and role prefetched with annotated member_count,
        eliminating N+1 queries when serializing nested roles.
        """
        return cls.objects.select_related('user').prefetch_related(
            Prefetch('role', queryset=Role._base_queryset())
        )

    @classmethod
    def get_all(cls, role_id=None, status=None, search=None):
        """Retrieve all team members with optional role, status, and search filters."""
        qs = cls._base_queryset().all()
        if role_id:
            qs = qs.filter(role_id=role_id)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(job_title__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(department__icontains=search)
            )
        return qs

    @classmethod
    def get_by_user(cls, user):
        """Retrieve team member by User instance or None."""
        try:
            return cls._base_queryset().get(user=user)
        except cls.DoesNotExist:
            return None

    @classmethod
    def create_member(
        cls,
        email,
        full_name,
        role_id=None,
        job_title='',
        phone_number='',
        department=Department.OPERATIONS,
        password=None,
        custom_permissions=None,
    ):
        """Create a new User and corresponding TeamMember profile directly."""
        User: Any = get_user_model()
        clean_email = email.strip().lower()
        clean_name = full_name.strip()

        # Split full name into first and last name
        parts = clean_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        # Deterministic or clean username based on email
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', clean_email.split('@')[0]) or 'member'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        raw_password = password or 'AxooraPass2026!'
        user = User.objects.create_user(
            username=username,
            email=clean_email,
            password=raw_password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
        )

        role = Role.get_by_id(role_id) if role_id else None
        perms = custom_permissions if isinstance(custom_permissions, list) else []

        member = cls.objects.create(
            user=user,
            role=role,
            job_title=job_title.strip(),
            phone_number=phone_number.strip(),
            department=department,
            status=MemberStatus.ACTIVE,
            custom_permissions=perms,
        )
        return member

    @classmethod
    def update_member(cls, member_id, **fields):
        """Update team member attributes and User attributes."""
        member = cls.get_by_id(member_id)
        if not member:
            return None

        user = member.user
        user_updated = False
        member_updated = False

        if 'full_name' in fields and fields['full_name'] is not None:
            parts = fields['full_name'].strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user_updated = True

        if 'email' in fields and fields['email'] is not None:
            user.email = fields['email'].strip().lower()
            user_updated = True

        if 'password' in fields and fields['password']:
            user.set_password(fields['password'])
            user_updated = True

        if user_updated:
            user.save()

        if 'role_id' in fields:
            member.role = Role.get_by_id(fields['role_id']) if fields['role_id'] else None
            member_updated = True

        if 'job_title' in fields and fields['job_title'] is not None:
            member.job_title = fields['job_title'].strip()
            member_updated = True

        if 'phone_number' in fields and fields['phone_number'] is not None:
            member.phone_number = fields['phone_number'].strip()
            member_updated = True

        if 'department' in fields and fields['department'] is not None:
            member.department = fields['department']
            member_updated = True

        if 'status' in fields and fields['status'] is not None:
            member.status = fields['status']
            member.user.is_active = (member.status == MemberStatus.ACTIVE)
            member.user.save(update_fields=['is_active'])
            member_updated = True

        if 'custom_permissions' in fields and fields['custom_permissions'] is not None:
            member.custom_permissions = fields['custom_permissions']
            member_updated = True

        if member_updated:
            member.save()

        return member

    @classmethod
    def delete_member(cls, member_id):
        """Delete member and underlying user."""
        member = cls.get_by_id(member_id)
        if not member:
            return False
        user = member.user
        member.delete()
        user.delete()
        return True
