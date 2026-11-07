from rest_framework import serializers
from .enums import WaitlistInterest, WaitlistStatus


class WaitlistLeadCreateSerializer(serializers.Serializer):
    """
    Explicit Serializer for incoming public waitlist registrations and business/POS applications.
    """
    reference_id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(max_length=255)
    whatsapp_number = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    city = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    state = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    interest = serializers.ChoiceField(choices=WaitlistInterest.choices, default=WaitlistInterest.BUSINESS)
    consent = serializers.BooleanField(default=True)
    source = serializers.CharField(max_length=100, required=False, default='website')
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    # Business Account & POS Application Fields
    business_type = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    cac_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    sector = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    pos_model = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    terminal_count = serializers.IntegerField(required=False, default=1)
    street_address = serializers.CharField(required=False, allow_blank=True, default='')
    settlement_type = serializers.CharField(max_length=50, required=False, allow_blank=True, default='instant')
    settlement_bank = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    settlement_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    settlement_account_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    application_ref = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    tracking_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    metadata = serializers.DictField(required=False, default=dict)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_full_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError("Please provide your real full name.")
        return cleaned

    def validate_whatsapp_number(self, value):
        cleaned = value.strip().replace(' ', '').replace('-', '')
        if len(cleaned) < 8:
            raise serializers.ValidationError("Please provide a valid WhatsApp phone number.")
        return cleaned


class WaitlistLeadDetailSerializer(serializers.Serializer):
    """
    Explicit Serializer for reading and updating waitlist leads in admin views and tracking.
    """
    id = serializers.UUIDField(read_only=True)
    reference_id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(max_length=255)
    whatsapp_number = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    city = serializers.CharField(max_length=120, allow_blank=True, default='')
    state = serializers.CharField(max_length=120, allow_blank=True, default='')
    business_name = serializers.CharField(max_length=255, allow_blank=True, default='')
    interest = serializers.ChoiceField(choices=WaitlistInterest.choices)
    consent = serializers.BooleanField()
    status = serializers.ChoiceField(choices=WaitlistStatus.choices)
    notes = serializers.CharField(allow_blank=True, required=False, default='')
    source = serializers.CharField(max_length=100, allow_blank=True, default='website')

    # Extended onboarding details
    business_type = serializers.CharField(allow_blank=True, default='')
    cac_number = serializers.CharField(allow_blank=True, default='')
    sector = serializers.CharField(allow_blank=True, default='')
    pos_model = serializers.CharField(allow_blank=True, default='')
    terminal_count = serializers.IntegerField(default=1)
    street_address = serializers.CharField(allow_blank=True, default='')
    settlement_type = serializers.CharField(allow_blank=True, default='instant')
    settlement_bank = serializers.CharField(allow_blank=True, default='')
    settlement_account_number = serializers.CharField(allow_blank=True, default='')
    settlement_account_name = serializers.CharField(allow_blank=True, default='')
    application_ref = serializers.CharField(allow_blank=True, default='')
    tracking_number = serializers.CharField(allow_blank=True, default='')
    metadata = serializers.DictField(default=dict)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

