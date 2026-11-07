from django.contrib import admin
from .models import Role, TeamMember


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_system', 'member_count', 'updated_at')
    list_filter = ('is_system', 'created_at')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('id', 'slug', 'created_at', 'updated_at')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role', 'department', 'job_title', 'status', 'created_at')
    list_filter = ('status', 'department', 'role', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'job_title', 'phone_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    actions = ('mark_as_active', 'mark_as_suspended')

    @admin.action(description='Activate selected team members')
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')

    @admin.action(description='Suspend selected team members')
    def mark_as_suspended(self, request, queryset):
        queryset.update(status='suspended')
