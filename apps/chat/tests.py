from typing import Any
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import ChatSession, ChatMessage, KnowledgeDocument, KnowledgeChunk
from .rag import retrieve_relevant_chunks, generate_rag_answer


class ChatApiTests(TestCase):
    def setUp(self):
        self.client: Any = APIClient()

        # Seed test knowledge doc and chunk
        self.doc = KnowledgeDocument.objects.create(
            title="Apex POS Terminal Specifications",
            slug="test-apex-pos",
            category="pos_hardware",
            content="The Apex POS has dual-eSIM (MTN and Airtel) and flat 0.4% rate with instant NIBSS settlement.",
        )
        self.chunk = KnowledgeChunk.objects.create(
            document=self.doc,
            chunk_title="Apex POS Dual eSIM & Settlement",
            content="The Apex POS has dual-eSIM (MTN and Airtel) and flat 0.4% rate with instant NIBSS settlement.",
            keywords="pos, apex, esim, mtn, airtel, rate, settlement",
            source_type="document",
        )

    def test_send_message_ai_answers_pos_question(self):
        url = reverse('chat-message')
        payload = {
            'text': 'How much does the Apex POS machine cost and what are the fees?',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertEqual(response.data['status'], 'ai_active')
        self.assertIn('Apex POS', response.data['reply']['text'])
        self.assertEqual(ChatMessage.objects.count(), 2)  # 1 user + 1 ai

    def test_send_message_triggers_human_escalation_intent(self):
        url = reverse('chat-message')
        payload = {
            'text': 'I need to speak with a real human agent please',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'escalated')
        self.assertIn('human customer agent', response.data['reply']['text'])
        self.assertTrue(response.data['reply']['is_escalation_trigger'])

        # Check session status in DB
        session = ChatSession.objects.get(id=response.data['session_id'])
        self.assertEqual(session.status, 'escalated')
        self.assertIsNotNone(session.escalated_at)

    def test_explicit_escalation_endpoint(self):
        session = ChatSession.objects.create(status='ai_active')
        url = reverse('chat-escalate')
        payload = {
            'session_id': str(session.session_id),
            'customer_name': 'Tunde Balogun',
            'customer_phone': '+2348021112233',
            'customer_email': 'tunde@example.com',
            'reason': 'Complex POS merchant settlement question',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('whatsapp_url', response.data)
        self.assertEqual(response.data['ticket_code'], session.ticket_code)

        session.refresh_from_db()
        self.assertEqual(session.status, 'escalated')
        self.assertEqual(session.customer_name, 'Tunde Balogun')
        self.assertEqual(session.customer_phone, '+2348021112233')

    def test_chat_history_retrieval(self):
        session = ChatSession.objects.create(customer_name='Hauwa')
        ChatMessage.objects.create(session=session, sender='user', text='Hello')
        ChatMessage.objects.create(session=session, sender='ai', text='Hi Hauwa! How can Axoora help?')

        url = reverse('chat-history', kwargs={'session_id': session.session_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 2)

    def test_rag_retrieves_relevant_chunks(self):
        chunks = retrieve_relevant_chunks("Does the Apex POS support MTN and Airtel dual eSIM?")
        self.assertGreaterEqual(len(chunks), 1)
        top = chunks[0]
        self.assertIn("Apex POS", top['title'])
        self.assertIn("0.4%", top['content'])

    def test_rag_query_endpoint(self):
        url = reverse('rag-query')
        payload = {
            'query': 'What is the rate and network support on the Apex POS terminal?',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('sources', response.data)
        self.assertIn('retrieved_chunks', response.data)
        self.assertGreaterEqual(len(response.data['retrieved_chunks']), 1)

    def test_live_cms_products_and_tracking_lookup_in_chat(self):
        from ..content.models import ProductItem
        from ..waitlist.models import WaitlistLead

        ProductItem.create_product(
            name='Paycircle Group Vault',
            category='personal',
            headline='Automated Ajo & Esusu Group Contributions',
            fee_structure='0% Group Contribution Fee',
            status='Active',
            highlight='Transparent ledger for every member',
            description='Collect and track rotational savings on WhatsApp.',
        )
        WaitlistLead.create_lead(
            full_name='Bilkisu Kano',
            whatsapp_number='+2348099887766',
            email='bilkisu@kano.ng',
            business_name='Bilkisu Grains',
            application_ref='AX-2026-9001',
            tracking_number='TRK-AX9001',
        )

        # 1. Ask about the newly added CMS product
        msg_url = reverse('chat-message')
        prod_res = self.client.post(msg_url, {'text': 'Tell me about Paycircle Group Vault'}, format='json')
        self.assertEqual(prod_res.status_code, status.HTTP_200_OK)
        self.assertIn('Paycircle Group Vault', prod_res.data['reply']['text'])

        # 2. Paste tracking code into chat
        trk_res = self.client.post(msg_url, {'text': 'Check status for AX-2026-9001'}, format='json')
        self.assertEqual(trk_res.status_code, status.HTTP_200_OK)
        self.assertIn('Bilkisu Grains', trk_res.data['reply']['text'])
        self.assertIn('TRK-AX9001', trk_res.data['reply']['text'])

    def test_agent_reply_and_session_lifecycle_management(self):
        session = ChatSession.objects.create(customer_name='Musa', status='escalated')
        reply_url = reverse('chat-agent-reply')
        reply_res = self.client.post(
            reply_url,
            {
                'session_id': str(session.session_id),
                'text': 'Hello Musa, I have reviewed your POS request.',
                'agent_name': 'Amina (Maitama Desk)',
            },
            format='json',
        )
        self.assertEqual(reply_res.status_code, status.HTTP_200_OK)
        self.assertEqual(reply_res.data['status'], 'human_active')
        self.assertIn('Amina (Maitama Desk)', reply_res.data['message']['text'])

        # Resolve ticket via detail endpoint
        detail_url = reverse('admin-chat-session-detail', kwargs={'session_id': session.session_id})
        patch_res = self.client.patch(detail_url, {'status': 'resolved'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['data']['status'], 'resolved')

        # Delete session
        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertTrue(del_res.data['success'])

    def test_inactivity_warn_and_disconnect(self):
        session = ChatSession.objects.create(customer_name='Chidi', status='human_active')
        inactivity_url = reverse('chat-inactivity')

        # 1. Warn
        warn_res = self.client.post(
            inactivity_url,
            {
                'session_id': str(session.session_id),
                'action': 'warn',
            },
            format='json',
        )
        self.assertEqual(warn_res.status_code, status.HTTP_200_OK)
        self.assertEqual(warn_res.data['action'], 'warn')
        self.assertIn('Inactivity Warning', warn_res.data['message']['text'])

        # 2. Disconnect
        disc_res = self.client.post(
            inactivity_url,
            {
                'session_id': str(session.session_id),
                'action': 'disconnect',
            },
            format='json',
        )
        self.assertEqual(disc_res.status_code, status.HTTP_200_OK)
        self.assertEqual(disc_res.data['action'], 'disconnect')
        self.assertEqual(disc_res.data['status'], 'closed')
        self.assertIn('disconnected due to customer inactivity', disc_res.data['message']['text'])

        session.refresh_from_db()
        self.assertEqual(session.status, 'closed')
        self.assertIsNotNone(session.resolved_at)

    def test_authenticated_agent_reply_locks_actual_name(self):
        from django.contrib.auth import get_user_model
        from apps.team.models import TeamMember, Role

        User = get_user_model()
        officer = User.objects.create_user(
            username='adaeze_officer',
            password='Password123!',
            first_name='Adaeze',
            last_name='Bello',
            email='adaeze@axoora.com',
        )
        role = Role.objects.create(name='Support Specialist', slug='support-specialist', permissions=['chat:*'])
        TeamMember.objects.create(
            user=officer,
            role=role,
            job_title='Senior Support Specialist',
            status='active',
        )

        session = ChatSession.objects.create(customer_name='Tunde', status='escalated')
        reply_url = reverse('chat-agent-reply')

        # Authenticate client as the officer
        self.client.force_authenticate(user=officer)

        # Attempt to reply while trying to spoof a different name
        res = self.client.post(
            reply_url,
            {
                'session_id': str(session.session_id),
                'text': 'Hello Tunde, looking into your transaction reversal right now.',
                'agent_name': 'Fake Impersonator',  # Spoof attempt must be ignored in favor of real name
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Verify message text and sender_name reflects genuine name
        self.assertIn('Adaeze Bello', res.data['message']['text'])
        self.assertNotIn('Fake Impersonator', res.data['message']['text'])
        self.assertEqual(res.data['message']['sender_name'], 'Adaeze Bello')

        # Check assigned agent on session
        session.refresh_from_db()
        self.assertEqual(session.assigned_agent, officer)

    def test_ticket_tracking_and_resolution_records_officer_and_notes(self):
        from django.contrib.auth import get_user_model
        from apps.team.models import TeamMember, Role

        User = get_user_model()
        officer = User.objects.create_user(
            username='musa_resolver',
            password='Password123!',
            first_name='Musa',
            last_name='Danladi',
            email='musa@axoora.com',
        )
        role = Role.objects.create(name='Desk Lead', slug='desk-lead', permissions=['chat:*'])
        TeamMember.objects.create(
            user=officer,
            role=role,
            job_title='Operations Lead',
            status='active',
        )

        session = ChatSession.objects.create(
            customer_name='Ibrahim',
            customer_phone='+2348039991122',
            issue_summary='POS settlement delayed',
            status='human_active',
        )

        detail_url = reverse('admin-chat-session-detail', kwargs={'session_id': session.session_id})
        self.client.force_authenticate(user=officer)

        resolve_res = self.client.patch(
            detail_url,
            {
                'status': 'resolved',
                'resolution_notes': 'NIP session queried. Funds returned to wallet successfully.',
            },
            format='json',
        )
        self.assertEqual(resolve_res.status_code, status.HTTP_200_OK)
        session_data = resolve_res.data['data']
        self.assertEqual(session_data['status'], 'resolved')
        self.assertEqual(session_data['resolved_by_name'], 'Musa Danladi')
        self.assertEqual(session_data['resolution_notes'], 'NIP session queried. Funds returned to wallet successfully.')
        self.assertIsNotNone(session_data['resolved_at'])

        # Verify query with tickets filter returns this resolved ticket
        list_url = reverse('admin-chat-sessions')
        track_res = self.client.get(f"{list_url}?status=tickets&search=Musa")
        self.assertEqual(track_res.status_code, status.HTTP_200_OK)
        self.assertEqual(track_res.data['count'], 1)
        self.assertEqual(track_res.data['results'][0]['resolved_by_name'], 'Musa Danladi')
