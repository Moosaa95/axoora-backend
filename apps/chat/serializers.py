from rest_framework import serializers
from .enums import ChatStatus, MessageSender


class ChatMessageSerializer(serializers.Serializer):
    """
    Explicit Serializer for chat transcript messages.
    """
    id = serializers.UUIDField(read_only=True)
    sender = serializers.ChoiceField(choices=MessageSender.choices)
    sender_name = serializers.CharField(required=False, allow_blank=True, default='')
    text = serializers.CharField()
    time = serializers.SerializerMethodField()
    suggested_actions = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    is_escalation_trigger = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)

    def get_time(self, obj):
        return obj.created_at.strftime('%H:%M')


class ChatSessionSerializer(serializers.Serializer):
    """
    Explicit Serializer for reading chat sessions with transcript.
    """
    id = serializers.UUIDField(read_only=True)
    session_id = serializers.UUIDField(read_only=True)
    ticket_code = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(allow_blank=True, default='')
    customer_phone = serializers.CharField(allow_blank=True, default='')
    customer_email = serializers.EmailField(allow_blank=True, default='')
    status = serializers.ChoiceField(choices=ChatStatus.choices)
    priority = serializers.CharField(default='normal')
    issue_summary = serializers.CharField(allow_blank=True, default='')
    escalation_reason = serializers.CharField(allow_blank=True, default='')
    escalated_at = serializers.DateTimeField(allow_null=True)
    resolved_at = serializers.DateTimeField(allow_null=True)
    resolved_by_name = serializers.CharField(allow_blank=True, default='')
    resolution_notes = serializers.CharField(allow_blank=True, default='')
    assigned_agent_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)

    def get_assigned_agent_name(self, obj):
        if getattr(obj, 'assigned_agent', None):
            return obj.assigned_agent.get_full_name() or obj.assigned_agent.username
        return ''


class ChatSendMessageInputSerializer(serializers.Serializer):
    """
    Input serializer for incoming user questions.
    """
    session_id = serializers.UUIDField(required=False, allow_null=True)
    text = serializers.CharField(max_length=2000)
    customer_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    customer_phone = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')


class ChatEscalateInputSerializer(serializers.Serializer):
    """
    Input serializer for customer human escalation requests.
    """
    session_id = serializers.UUIDField(required=True)
    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=50)
    customer_email = serializers.EmailField(required=False, allow_blank=True, default='')
    reason = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')


class ChatAgentReplyInputSerializer(serializers.Serializer):
    """
    Input serializer for human support agent replies.
    """
    session_id = serializers.UUIDField(required=True)
    text = serializers.CharField(max_length=2000)
    agent_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
