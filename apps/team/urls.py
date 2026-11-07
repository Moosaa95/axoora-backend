from django.urls import path
from .views import (
    AuthLoginView,
    AuthMeView,
    AuthLogoutView,
    ChangePasswordView,
    CsrfTokenView,
    AvailablePermissionsView,
    RoleListView,
    RoleDetailView,
    TeamMemberListView,
    TeamMemberDetailView,
)

urlpatterns = [
    # Manager Authentication
    path('auth/csrf/', CsrfTokenView.as_view(), name='auth-csrf'),
    path('auth/login/', AuthLoginView.as_view(), name='auth-login'),
    path('auth/me/', AuthMeView.as_view(), name='auth-me'),
    path('auth/logout/', AuthLogoutView.as_view(), name='auth-logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # Permissions Registry
    path('permissions/', AvailablePermissionsView.as_view(), name='team-permissions'),

    # Roles Management (RBAC)
    path('roles/', RoleListView.as_view(), name='team-roles-list'),
    path('roles/<uuid:role_id>/', RoleDetailView.as_view(), name='team-roles-detail'),

    # Team Members Directory
    path('members/', TeamMemberListView.as_view(), name='team-members-list'),
    path('members/<uuid:member_id>/', TeamMemberDetailView.as_view(), name='team-members-detail'),
]
