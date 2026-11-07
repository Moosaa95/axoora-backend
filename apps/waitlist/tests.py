from typing import Any
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import WaitlistLead
from .enums import WaitlistInterest, WaitlistStatus


class WaitlistApiTests(TestCase):
    def setUp(self):
        self.client: Any = APIClient()

    def test_waitlist_submission_success(self):
        url = reverse('waitlist-submit')
        payload = {
            'full_name': 'Test User',
            'whatsapp_number': '+2348012345678',
            'email': 'test@axoora.ai',
            'city': 'Abuja',
            'interest': 'business',
            'consent': True,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(WaitlistLead.objects.count(), 1)
        lead = WaitlistLead.objects.first()
        self.assertIsNotNone(lead)
        assert lead is not None
        self.assertEqual(lead.full_name, 'Test User')
        self.assertEqual(lead.interest, 'business')

    def test_waitlist_submission_validation_error(self):
        url = reverse('waitlist-submit')
        payload = {
            'full_name': '',  # invalid
            'whatsapp_number': '123',  # invalid
            'email': 'not-an-email',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_classmethods_query(self):
        lead = WaitlistLead.create_lead(
            full_name='Aminu Kano',
            whatsapp_number='+2348091122334',
            email='aminu@example.com',
            interest=WaitlistInterest.POS_AGENT,
        )
        self.assertIsNotNone(lead.id)
        self.assertIsNotNone(lead.reference_id)

        # Test classmethod get_all
        all_leads = WaitlistLead.get_all(interest=WaitlistInterest.POS_AGENT)
        self.assertEqual(all_leads.count(), 1)

        # Test classmethod get_by_id
        fetched = WaitlistLead.get_by_id(lead.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.full_name, 'Aminu Kano')

        # Test classmethod update_status
        updated = WaitlistLead.update_lead_status(lead.id, new_status=WaitlistStatus.CONTACTED)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.status, WaitlistStatus.CONTACTED)

    def test_business_onboarding_submission_and_tracking(self):
        url = reverse('waitlist-submit')
        payload = {
            'full_name': 'Fatima Aliyu',
            'whatsapp_number': '+2348033221100',
            'email': 'fatima@aliyuenterprises.ng',
            'business_name': 'Aliyu Retail Ltd',
            'business_type': 'ltd',
            'cac_number': 'RC-1928374',
            'sector': 'retail',
            'pos_model': 'ax-smart',
            'terminal_count': 3,
            'city': 'Abuja',
            'state': 'FCT',
            'street_address': 'Plot 402 Constitution Avenue, Central Area',
            'interest': 'pos-agent',
            'application_ref': 'AX-99123',
            'tracking_number': 'AX-DEL-7788',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['application_ref'], 'AX-99123')
        self.assertEqual(response.data['tracking_number'], 'AX-DEL-7788')

        # Test tracking endpoint via application_ref
        track_url = reverse('waitlist-track', kwargs={'tracking_code': 'AX-99123'})
        track_res = self.client.get(track_url)
        self.assertEqual(track_res.status_code, status.HTTP_200_OK)
        self.assertTrue(track_res.data['found'])
        self.assertEqual(track_res.data['business_name'], 'Aliyu Retail Ltd')
        self.assertEqual(track_res.data['terminal_count'], 3)

        # Test tracking endpoint via tracking_number
        track_ship_url = reverse('waitlist-track', kwargs={'tracking_code': 'AX-DEL-7788'})
        track_ship_res = self.client.get(track_ship_url)
        self.assertEqual(track_ship_res.status_code, status.HTTP_200_OK)
        self.assertTrue(track_ship_res.data['found'])

        # Test invalid tracking code
        not_found_res = self.client.get(reverse('waitlist-track', kwargs={'tracking_code': 'DOESNOTEXIST'}))
        self.assertEqual(not_found_res.status_code, status.HTTP_404_NOT_FOUND)

