from typing import Any
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import HeroConfiguration, JournalArticle, FaqItem


class ContentApiTests(TestCase):
    def setUp(self):
        self.client: Any = APIClient()
        HeroConfiguration.objects.create(
            headline_business='Money, simplified for the street.',
        )
        JournalArticle.objects.create(
            slug='test-article',
            title='Test Article Title',
            summary='Test Summary',
            category='Engineering',
        )
        FaqItem.objects.create(
            question='Is Axoora licensed?',
            answer='Yes, licensed by CBN.',
            category='General',
        )

    def test_hero_endpoint(self):
        url = reverse('hero-config')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['headline_business'], 'Money, simplified for the street.')

    def test_articles_endpoint(self):
        url = reverse('journal-articles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', [])), 1)

    def test_faqs_endpoint(self):
        url = reverse('faqs-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', [])), 1)

    def test_article_crud_by_slug_and_uuid(self):
        list_url = reverse('journal-articles-list')
        create_res = self.client.post(
            list_url,
            {
                'title': 'Axoora Launches Instant Settlement',
                'summary': 'Sub-second NIBSS clearing for street merchants.',
                'category': 'News',
                'content': 'Full article content body.',
                'author': 'Axoora Newsroom',
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        article_id = create_res.data['data']['id']
        article_slug = create_res.data['data']['slug']

        # Update via UUID (as frontend AdminDashboard does)
        uuid_url = reverse('journal-articles-detail', kwargs={'slug': article_id})
        patch_res = self.client.patch(uuid_url, {'title': 'Updated Title via UUID'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['data']['title'], 'Updated Title via UUID')

        # Retrieve via slug
        slug_url = reverse('journal-articles-detail', kwargs={'slug': article_slug})
        get_res = self.client.get(slug_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['title'], 'Updated Title via UUID')

        # Delete via UUID
        del_res = self.client.delete(uuid_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertTrue(del_res.data['success'])

    def test_bootstrap_and_onboarding_steps_persistence(self):
        boot_url = reverse('content-bootstrap')
        res = self.client.get(boot_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('hero', res.data)
        self.assertIn('stories', res.data)
        self.assertIn('products', res.data)
        self.assertIn('articles', res.data)
        self.assertIn('onboarding_steps', res.data['hero'])

        # Persist updated onboarding steps via hero PUT
        hero_url = reverse('hero-config')
        custom_steps = [{'num': 1, 'tag': '01. Fast', 'title': 'Custom Step 1'}]
        put_res = self.client.put(hero_url, {'onboarding_steps': custom_steps}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['onboarding_steps'], custom_steps)

    def test_story_and_product_resilient_upsert_with_local_id(self):
        story_url = reverse('merchant-stories-detail', kwargs={'story_id': 'bilkisu'})
        patch_story = self.client.patch(
            story_url,
            {
                'name': 'Hajiya Bilkisu Danladi',
                'role': 'Wholesale Grain Merchant',
                'location': 'Kano',
                'quote': 'Instant settlement works great.',
            },
            format='json',
        )
        self.assertEqual(patch_story.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_story.data['data']['name'], 'Hajiya Bilkisu Danladi')

        product_url = reverse('products-detail', kwargs={'product_id': 'prod-pos'})
        patch_prod = self.client.patch(
            product_url,
            {
                'name': 'Axoora Apex Pro Smart POS',
                'category': 'hardware',
                'headline': 'Dual-SIM 4G Terminal',
                'fee_structure': '0.5% capped',
                'status': 'Active',
                'highlight': '99.98% Uptime',
                'description': 'Ruggedized terminal.',
            },
            format='json',
        )
        self.assertEqual(patch_prod.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_prod.data['data']['name'], 'Axoora Apex Pro Smart POS')

    def test_faq_crud_and_bootstrap_sync(self):
        # Verify faqs in bootstrap
        boot_url = reverse('content-bootstrap')
        res = self.client.get(boot_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('faqs', res.data)
        self.assertGreaterEqual(len(res.data['faqs']), 1)

        # Create FAQ via POST
        create_res = self.client.post(
            reverse('faqs-list'),
            {
                'question': 'How do I fund my wallet?',
                'answer': 'Transfer from any Nigerian bank to your dedicated Axoora NUBAN.',
                'category': 'General',
                'order': 1,
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        faq_id = create_res.data['data']['id']

        # Update FAQ via PATCH
        patch_res = self.client.patch(
            reverse('faqs-detail', kwargs={'faq_id': faq_id}),
            {'question': 'How do I fund my wallet instantly?'},
            format='json',
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['data']['question'], 'How do I fund my wallet instantly?')

        # Delete FAQ
        del_res = self.client.delete(reverse('faqs-detail', kwargs={'faq_id': faq_id}))
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertTrue(del_res.data['success'])
