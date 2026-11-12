from django.urls import path
from .views import (
    ChatSendMessageView,
    ChatEscalateView,
    ChatSessionHistoryView,
    ChatAgentReplyView,
    ChatInactivityView,
    ChatSessionListView,
    ChatSessionDetailView,
    RagQueryView,
)

urlpatterns = [
    path('message/', ChatSendMessageView.as_view(), name='chat-message'),
    path('escalate/', ChatEscalateView.as_view(), name='chat-escalate'),
    path('history/<uuid:session_id>/', ChatSessionHistoryView.as_view(), name='chat-history'),
    path('agent-reply/', ChatAgentReplyView.as_view(), name='chat-agent-reply'),
    path('inactivity/', ChatInactivityView.as_view(), name='chat-inactivity'),
    path('sessions/', ChatSessionListView.as_view(), name='admin-chat-sessions'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='admin-chat-session-detail'),
    path('rag/query/', RagQueryView.as_view(), name='rag-query'),
]
