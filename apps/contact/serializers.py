from rest_framework import serializers
from .enums import InquiryCategory, InquiryStatus


class ContactInquiryCreateSerializer(serializers.Serializer):
    """
    Explicit Serializer for incoming public contact inquiries.
    """
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(choices=InquiryCategory.choices, default=InquiryCategory.GENERAL)
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()

    def validate_message(self, value):
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise serializers.ValidationError("Please provide at least 10 characters in your message.")
        return cleaned


class ContactInquiryDetailSerializer(serializers.Serializer):
    """
    Explicit Serializer for staff review of contact inquiries.
    """
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True, default='')
    category = serializers.ChoiceField(choices=InquiryCategory.choices)
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    status = serializers.ChoiceField(choices=InquiryStatus.choices)
    response_notes = serializers.CharField(allow_blank=True, default='')
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
