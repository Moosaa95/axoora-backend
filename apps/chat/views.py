from typing import Any, cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..common.pagination import paginate_queryset
from .models import ChatSession, ChatMessage
from .enums import ChatStatus, MessageSender
from .serializers import (
    ChatMessageSerializer,
    ChatSessionSerializer,
    ChatSendMessageInputSerializer,
    ChatEscalateInputSerializer,
    ChatAgentReplyInputSerializer,
)
from .services import generate_ai_response, get_whatsapp_escalation_url
from .rag import retrieve_relevant_chunks, generate_rag_answer


class ChatSendMessageView(APIView):
    """
    Public endpoint for live chat:
    Receives customer questions, generates AI domain answers, or triggers human escalation.
    Uses model classmethods on ChatSession and ChatMessage.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatSendMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # 1. Retrieve or create session via model classmethod
        session = ChatSession.get_or_create_session(
            session_id=data.get('session_id'),
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 2. Record Customer Message via model classmethod
        ChatMessage.create_message(
            session=session,
            sender=MessageSender.USER,
            text=data['text'],
        )

        # 3. Check if human agent is currently handling this session
        if session.status == ChatStatus.HUMAN_ACTIVE:
            ai_reply_text = (
                "Your conversation is currently connected to an Axoora live support agent. "
                "An officer is reviewing your latest message and will reply in this chat momentarily."
            )
            reply_msg = ChatMessage.create_message(
                session=session,
                sender=MessageSender.SYSTEM,
                text=ai_reply_text,
                suggested_actions=[
                    {"label": "WhatsApp Desk Instead", "action": "open_url", "url": get_whatsapp_escalation_url(session, data['text']), "primary": True},
                    {"label": "Continue with AI Assistant", "action": "continue_ai"},
                ],
            )
            return Response({
                "session_id": str(session.session_id),
                "ticket_code": session.ticket_code,
                "status": session.status,
                "reply": ChatMessageSerializer(reply_msg).data,
            })

        # 4. Generate AI response (RAG grounded answering or human escalation)
        reply_text, suggested_actions, is_escalation = generate_ai_response(session, data['text'])

        reply_msg = ChatMessage.create_message(
            session=session,
            sender=MessageSender.AI,
            text=reply_text,
            suggested_actions=suggested_actions,
            is_escalation_trigger=is_escalation,
        )

        return Response({
            "session_id": str(session.session_id),
            "ticket_code": session.ticket_code,
            "status": session.status,
            "reply": ChatMessageSerializer(reply_msg).data,
        })


class ChatEscalateView(APIView):
    """
    Explicit endpoint for customer to submit contact info for priority human escalation.
    Uses model classmethods ChatSession.escalate_session() and ChatMessage.create_message().
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatEscalateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        session = ChatSession.escalate_session(
            session_id=data['session_id'],
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_email=data.get('customer_email', ''),
            reason=data.get('reason', ''),
        )
        if not session:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        wa_url = get_whatsapp_escalation_url(session, data.get('reason', 'Human support escalation'))

        # Add system confirmation message to transcript
        system_msg = ChatMessage.create_message(
            session=session,
            sender=MessageSender.SYSTEM,
            text=(
                f"Priority ticket #{session.ticket_code} created for {session.customer_name}. "
                f"A dedicated customer agent from our Maitama desk has been dispatched to assist you on WhatsApp ({session.customer_phone}) "
                f"or continue here."
            ),
            suggested_actions=[
                {"label": "💬 Open WhatsApp With Officer Now", "action": "open_url", "url": wa_url, "primary": True},
            ],
            is_escalation_trigger=True,
        )

        return Response({
            "success": True,
            "session_id": str(session.session_id),
            "ticket_code": session.ticket_code,
            "whatsapp_url": wa_url,
            "status": session.status,
            "message": "Human agent escalation successfully initiated.",
            "transcript_message": ChatMessageSerializer(system_msg).data,
        })


class ChatSessionHistoryView(APIView):
    """
    Retrieve full transcript of a chat session.
    Uses model classmethod ChatSession.get_by_session_id().
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, session_id):
        session = ChatSession.get_by_session_id(session_id)
        if not session:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ChatSessionSerializer(session).data)


class ChatAgentReplyView(APIView):
    """
    Staff / Agent endpoint to reply directly to a customer in the chat session.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ChatAgentReplyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        session = ChatSession.get_by_session_id(data['session_id'])
        if not session:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        session.status = ChatStatus.HUMAN_ACTIVE
        session.save(update_fields=['status', 'updated_at'])

        custom_agent = str(data.get('agent_name') or '').strip()
        agent_name = custom_agent or (request.user.get_full_name() if request.user.is_authenticated else '') or 'Support Officer'

        msg = ChatMessage.create_message(
            session=session,
            sender=MessageSender.AGENT,
            text=f"[{agent_name}]: {data['text']}",
        )

        return Response({
            "success": True,
            "status": session.status,
            "message": ChatMessageSerializer(msg).data,
        })


class ChatSessionListView(APIView):
    """
    Staff/Admin endpoint to view, search, and paginate all active customer chat sessions.
    Uses model classmethod ChatSession.get_all_sessions().
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get('status')
        search_filter = request.query_params.get('search')
        queryset = ChatSession.get_all_sessions(status=status_filter, search=search_filter)

        paginator, page = paginate_queryset(queryset, request, page_size=30)
        serializer = ChatSessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ChatSessionDetailView(APIView):
    """
    Update session status (resolve, return to AI, close) or delete a session.
    """
    permission_classes = [permissions.AllowAny]

    def patch(self, request, session_id):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        updated = ChatSession.update_session(session_id, **data)
        if not updated:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = data.get('status')
        if new_status == ChatStatus.RESOLVED:
            ChatMessage.create_message(
                session=updated,
                sender=MessageSender.SYSTEM,
                text=f"Ticket #{updated.ticket_code} has been marked as resolved by our support desk. Reply anytime to reopen.",
            )
        elif new_status == ChatStatus.AI_ACTIVE:
            ChatMessage.create_message(
                session=updated,
                sender=MessageSender.SYSTEM,
                text="Switched back to Axoora AI Concierge. Ask any question below!",
            )

        refreshed = ChatSession.get_by_session_id(session_id) or updated
        return Response({
            "success": True,
            "data": ChatSessionSerializer(refreshed).data,
        })

    def delete(self, request, session_id):
        deleted = ChatSession.delete_by_id(session_id)
        if not deleted:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Chat session deleted."})


class RagQueryView(APIView):
    """
    RAG Explorer Endpoint:
    Directly query the RAG retriever and grounded generation pipeline.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        req_data: dict[str, Any] = cast(dict[str, Any], request.data)
        query = str(req_data.get('query', '')).strip()
        top_k = int(req_data.get('top_k', 3))
        if not query:
            return Response({"error": "A query string is required."}, status=status.HTTP_400_BAD_REQUEST)

        chunks = retrieve_relevant_chunks(query, top_k=top_k)
        answer, sources, suggested_actions = generate_rag_answer(query, chunks)

        return Response({
            "query": query,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": chunks,
            "suggested_actions": suggested_actions,
        })
