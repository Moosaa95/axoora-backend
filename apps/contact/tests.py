from typing import Any
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import ContactInquiry


class ContactApiTests(TestCase):
    def setUp(self):
        self.client: Any = APIClient()

    def test_contact_submission_success(self):
        url = reverse('contact-submit')
        payload = {
            'full_name': 'Test Contact',
            'email': 'contact@example.com',
            'phone': '+2348099887766',
            'category': 'business',
            'subject': 'Inquiry about corporate partnership',
            'message': 'We would like to integrate our wholesale inventory network with Axoora terminals.',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(ContactInquiry.objects.count(), 1)
