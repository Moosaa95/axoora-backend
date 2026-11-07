from typing import Any
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Role, TeamMember
from .enums import MemberStatus, Department, ALL_PERMISSION_IDS


class TeamApiTests(TestCase):
    def setUp(self):
        self.client: Any = APIClient()
        # Create standard test roles
        self.admin_role = Role.objects.create(
            name='Test Administrator',
            slug='test-administrator',
            description='Test full access admin',
            is_system=True,
            permissions=ALL_PERMISSION_IDS,
        )
        self.editor_role = Role.objects.create(
            name='Test Editor',
            slug='test-editor',
            description='Test content editor',
            permissions=[
                'content.view',
                'content.manage',
            ],
        )

        # Create test users and team members
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@axoora.test',
            password='Password123!',
            first_name='Admin',
            last_name='User',
        )
        self.admin_member = TeamMember.objects.create(
            user=self.admin_user,
            role=self.admin_role,
            status=MemberStatus.ACTIVE,
            job_title='Chief Officer',
            department=Department.EXECUTIVE,
        )

    def test_login_success(self):
        url = reverse('auth-login')
        payload = {
            'username': 'admin_test',
            'password': 'Password123!',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data['user']['username'], 'admin_test')

    def test_login_invalid_credentials(self):
        url = reverse('auth-login')
        payload = {
            'username': 'admin_test',
            'password': 'WrongPassword!',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_get_current_session_authenticated(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('auth-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('authenticated'))
        self.assertEqual(response.data['user']['email'], 'admin@axoora.test')

    def test_get_roles_list(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('team-roles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_create_role(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('team-roles-list')
        payload = {
            'name': 'Support Specialist',
            'description': 'Handles live chats and waitlist inquiries',
            'permissions': ['leads.view', 'leads.manage'],
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'Support Specialist')
        self.assertEqual(response.data['data']['permissions'], ['leads.view', 'leads.manage'])

    def test_permissions_endpoint(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('team-permissions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('permissions', response.data)
        self.assertIn('flat', response.data)
        self.assertIn('grouped', response.data)
        self.assertGreaterEqual(len(response.data['flat']), 10)

    def test_logout(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('auth-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))

    def test_member_crud_and_filtering(self):
        self.client.login(username='admin_test', password='Password123!')
        url = reverse('team-members-list')

        # Create member with role_id and custom_permissions
        payload = {
            'full_name': 'Zainab Lawal',
            'email': 'zainab@axoora.test',
            'role_id': str(self.editor_role.id),
            'job_title': 'Senior Content Lead',
            'phone_number': '+2348011223344',
            'department': 'marketing',
            'custom_permissions': ['leads.view'],
        }
        create_res = self.client.post(url, payload, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        member_id = create_res.data['data']['id']
        self.assertIn('leads.view', create_res.data['data']['custom_permissions'])
        self.assertIn('leads.view', create_res.data['data']['effective_permissions'])
        self.assertIn('content.manage', create_res.data['data']['effective_permissions'])

        # Filter by role_id query param (as used by frontend)
        filter_res = self.client.get(f"{url}?role_id={self.editor_role.id}")
        self.assertEqual(filter_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(filter_res.data['results']), 1)
        self.assertEqual(filter_res.data['results'][0]['email'], 'zainab@axoora.test')

        # Update member
        detail_url = reverse('team-members-detail', kwargs={'member_id': member_id})
        patch_res = self.client.patch(detail_url, {'job_title': 'VP Marketing', 'status': 'suspended'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['data']['job_title'], 'VP Marketing')
        self.assertEqual(patch_res.data['data']['status'], 'suspended')

        # Delete member
        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertTrue(del_res.data['success'])

    def test_no_n_plus_one_queries_on_roles_and_members(self):
        from .serializers import RoleSerializer, TeamMemberSerializer

        for i in range(5):
            role = Role.create_role(name=f'Custom Role {i}', permissions=['content.view'])
            TeamMember.create_member(
                email=f'member{i}@axoora.test',
                full_name=f'Member {i}',
                role_id=role.id,
            )

        # Serializing all roles (7 roles total) must execute only 1 SQL query (annotated Count)
        with self.assertNumQueries(1):
            roles = list(Role.get_all())
            _ = RoleSerializer(roles, many=True).data

        # Serializing all team members (6 members + nested roles + member_count) must execute only 2 queries:
        # 1) SELECT team_members INNER JOIN auth_user
        # 2) SELECT team_roles with annotated COUNT(team_members.id) via Prefetch
        with self.assertNumQueries(2):
            members = list(TeamMember.get_all())
            _ = TeamMemberSerializer(members, many=True).data
