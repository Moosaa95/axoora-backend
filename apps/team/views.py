from __future__ import annotations

from typing import Any, cast
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..common.pagination import paginate_queryset
from .models import Role, TeamMember
from .enums import SYSTEM_PERMISSIONS, MemberStatus, Department
from .email_service import send_team_invite_email, send_password_reset_email
from .serializers import (
    RoleSerializer,
    RoleCreateUpdateSerializer,
    TeamMemberSerializer,
    TeamMemberCreateSerializer,
    TeamMemberUpdateSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)


def get_or_create_team_profile(user):
    """Ensure every staff/admin user has an associated TeamMember profile."""
    profile = TeamMember.get_by_user(user)
    if profile:
        return profile

    super_admin_role = Role._base_queryset().filter(is_system=True).first()
    if not super_admin_role:
        super_admin_role = Role.objects.create(
            name='Super Admin',
            slug='super-admin',
            description='Full system superuser access across all modules',
            permissions=['*'],
            is_system=True,
        )
        super_admin_role._member_count = 1

    return TeamMember.objects.create(
        user=user,
        role=super_admin_role,
        job_title='System Administrator' if user.is_superuser else 'Staff Member',
        department=Department.EXECUTIVE if user.is_superuser else Department.OPERATIONS,
        status=MemberStatus.ACTIVE,
    )


@method_decorator(csrf_exempt, name='dispatch')
class AuthLoginView(APIView):
    """
    Team Manager login endpoint. Accepts username or email and password.
    Returns serialized user profile with role and effective permissions.
    CSRF is exempted — protected by CORS + credentials policy.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login_data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        raw_identifier = login_data['username'].strip()
        raw_password = login_data['password']

        User: Any = get_user_model()
        user: Any = authenticate(request, username=raw_identifier, password=raw_password)

        if not user and '@' in raw_identifier:
            matched_user = User.objects.filter(email__iexact=raw_identifier).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=raw_password)

        if not user:
            return Response(
                {"error": "Invalid email/username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "This account is currently deactivated. Contact a Super Admin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Log user into Django session
        login(request, user)

        # Ensure TeamMember record exists
        profile = get_or_create_team_profile(user)

        # If user was in invited state, accept and activate on first login
        if profile.status == MemberStatus.INVITED:
            profile.status = MemberStatus.ACTIVE
            profile.save(update_fields=['status', 'updated_at'])

        return Response({
            "success": True,
            "message": f"Welcome back, {profile.full_name}.",
            "user": TeamMemberSerializer(profile).data,
            "permissions": profile.get_effective_permissions(),
        })


class AuthMeView(APIView):
    """
    Retrieve the profile and permissions of the currently authenticated manager.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"authenticated": False, "user": None, "permissions": []},
                status=status.HTTP_200_OK,
            )

        profile = get_or_create_team_profile(request.user)
        return Response({
            "authenticated": True,
            "user": TeamMemberSerializer(profile).data,
            "permissions": profile.get_effective_permissions(),
        })


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    """GET this endpoint to receive the csrftoken cookie before posting."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": request.META.get('CSRF_COOKIE', '')})


@method_decorator(csrf_exempt, name='dispatch')
class AuthLogoutView(APIView):
    """
    Log out the current manager and destroy the session.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({"success": True, "message": "Successfully logged out."})


class ChangePasswordView(APIView):
    """
    Allows authenticated managers to change their password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        user = request.user
        if not user.check_password(data['old_password']):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data['new_password'])
        user.save()
        login(request, user)
        return Response({"success": True, "message": "Password changed successfully."})


class AvailablePermissionsView(APIView):
    """
    Returns the comprehensive list of available system permissions grouped by module.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories: dict[str, list[dict[str, str]]] = {}
        for perm in SYSTEM_PERMISSIONS:
            cat = perm['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'id': perm['id'],
                'label': perm['name'],
                'description': perm['description'],
            })

        grouped = [
            {'group': cat, 'permissions': perms}
            for cat, perms in categories.items()
        ]

        return Response({
            "permissions": grouped,
            "flat": SYSTEM_PERMISSIONS,
            "grouped": categories,
        })


class RoleListView(APIView):
    """
    List all roles or create a new custom role with assigned permissions.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        roles = Role.get_all()
        data = RoleSerializer(roles, many=True).data
        return Response({
            "count": len(data),
            "results": data,
        })

    def post(self, request):
        serializer = RoleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        # Check for duplicate name
        if Role.objects.filter(name__iexact=data['name'].strip()).exists():
            return Response(
                {"error": f"A role named '{data['name']}' already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = Role.create_role(
            name=data['name'],
            description=data.get('description', ''),
            permissions=data.get('permissions', []),
        )

        return Response(
            {
                "success": True,
                "message": f"Role '{role.name}' created successfully.",
                "data": RoleSerializer(role).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RoleDetailView(APIView):
    """
    Retrieve, update or delete a specific role.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, role_id):
        role = Role.get_by_id(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoleSerializer(role).data)

    def patch(self, request, role_id):
        role = Role.get_by_id(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        data: dict[str, Any] = cast(dict[str, Any], request.data)
        updated_role = Role.update_role(
            role_id=role_id,
            name=data.get('name'),
            description=data.get('description'),
            permissions=data.get('permissions'),
        )
        return Response({
            "success": True,
            "message": f"Role '{role.name}' updated successfully.",
            "data": RoleSerializer(updated_role).data,
        })

    def delete(self, request, role_id):
        role = Role.get_by_id(role_id)
        if not role:
            return Response({"error": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        if role.is_system:
            return Response(
                {"error": "System protected roles cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Role.delete_role(role_id)
        return Response({"success": True, "message": "Role deleted successfully."})


class TeamMemberListView(APIView):
    """
    List team members or create a new team member with immediate role assignment.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        role_filter = request.query_params.get('role') or request.query_params.get('role_id')
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')

        queryset = TeamMember.get_all(
            role_id=role_filter,
            status=status_filter,
            search=search_query,
        )
        paginator, page = paginate_queryset(queryset, request)
        serializer = TeamMemberSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TeamMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        User: Any = get_user_model()
        if User.objects.filter(email__iexact=data['email'].strip()).exists():
            return Response(
                {"error": f"A user with email '{data['email']}' already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = TeamMember.create_member(
            email=data['email'],
            full_name=data['full_name'],
            role_id=data.get('role_id'),
            job_title=data.get('job_title', ''),
            phone_number=data.get('phone_number', ''),
            department=data.get('department', Department.OPERATIONS),
            password=data.get('password'),
            custom_permissions=data.get('custom_permissions'),
        )

        initial_password = getattr(member, '_initial_password', None)
        email_sent = False
        if initial_password:
            email_sent = send_team_invite_email(member, initial_password, request=request)

        return Response(
            {
                "success": True,
                "message": f"Team member '{member.full_name}' invited successfully. {'Invitation email dispatched.' if email_sent else 'Credentials generated.'}",
                "data": TeamMemberSerializer(member).data,
                "generated_password": initial_password,
                "email_sent": email_sent,
            },
            status=status.HTTP_201_CREATED,
        )


class TeamMemberDetailView(APIView):
    """
    Retrieve, update or remove a team member.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, member_id):
        member = TeamMember.get_by_id(member_id)
        if not member:
            return Response({"error": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TeamMemberSerializer(member).data)

    def patch(self, request, member_id):
        member = TeamMember.get_by_id(member_id)
        if not member:
            return Response({"error": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TeamMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        updated = TeamMember.update_member(member_id, **data)
        return Response({
            "success": True,
            "message": f"Team member '{member.full_name}' updated successfully.",
            "data": TeamMemberSerializer(updated).data,
        })

    def delete(self, request, member_id):
        deleted = TeamMember.delete_member(member_id)
        if not deleted:
            return Response({"error": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Team member removed successfully."})


class TeamMemberResetPasswordView(APIView):
    """
    Admin resets a team member's password, generating a new secure temporary password
    and dispatching an email notification.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, member_id):
        new_pwd_input = request.data.get('new_password')
        member, new_pwd = TeamMember.reset_password(member_id, new_password=new_pwd_input)
        if not member:
            return Response({"error": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)

        email_sent = send_password_reset_email(member, new_pwd, request=request)
        return Response({
            "success": True,
            "message": f"Password for '{member.full_name}' reset successfully. {'Notification dispatched to email.' if email_sent else 'Ready for copy.'}",
            "new_password": new_pwd,
            "email_sent": email_sent,
        })


class TeamMemberResendInviteView(APIView):
    """
    Admin resends the invitation email with newly generated temporary credentials
    if the team member hasn't accepted yet.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, member_id):
        member, new_pwd = TeamMember.reset_password(member_id)
        if not member:
            return Response({"error": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure status reflects invited if not yet logged in
        if not member.user.last_login:
            member.status = MemberStatus.INVITED
            member.save(update_fields=['status', 'updated_at'])

        email_sent = send_team_invite_email(member, new_pwd, request=request)
        return Response({
            "success": True,
            "message": f"Invitation email resent to {member.email}.",
            "temporary_password": new_pwd,
            "email_sent": email_sent,
        })
