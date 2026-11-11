from rest_framework import serializers
from .models import Role, TeamMember
from .enums import MemberStatus, Department


class RoleSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=120)
    slug = serializers.CharField(read_only=True)
    description = serializers.CharField(allow_blank=True, default='')
    permissions = serializers.ListField(child=serializers.CharField(), default=list)
    is_system = serializers.BooleanField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class RoleCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    permissions = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError("Role name must be at least 2 characters.")
        return cleaned


class TeamMemberSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    job_title = serializers.CharField(allow_blank=True, default='')
    phone_number = serializers.CharField(allow_blank=True, default='')
    department = serializers.CharField()
    status = serializers.ChoiceField(choices=MemberStatus.choices)
    role = RoleSerializer(read_only=True)
    custom_permissions = serializers.ListField(child=serializers.CharField(), read_only=True)
    effective_permissions = serializers.ListField(child=serializers.CharField(), source='get_effective_permissions', read_only=True)
    has_accepted = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_has_accepted(self, obj) -> bool:
        return obj.user.last_login is not None


class TeamMemberCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    role_id = serializers.UUIDField(required=False, allow_null=True)
    job_title = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    phone_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    department = serializers.ChoiceField(choices=Department.choices, default=Department.OPERATIONS)
    password = serializers.CharField(required=False, allow_blank=True, default='')
    custom_permissions = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_full_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters.")
        return cleaned


class TeamMemberUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    role_id = serializers.UUIDField(required=False, allow_null=True)
    job_title = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    department = serializers.ChoiceField(choices=Department.choices, required=False)
    status = serializers.ChoiceField(choices=MemberStatus.choices, required=False)
    password = serializers.CharField(required=False, allow_blank=True)
    custom_permissions = serializers.ListField(child=serializers.CharField(), required=False)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()  # Can be username or email
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
