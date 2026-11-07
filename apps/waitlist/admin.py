from django.contrib import admin
from .models import WaitlistLead


@admin.register(WaitlistLead)
class WaitlistLeadAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'application_ref',
        'interest',
        'business_name',
        'pos_model',
        'terminal_count',
        'city',
        'status',
        'tracking_number',
        'created_at',
    )
    list_filter = ('status', 'interest', 'pos_model', 'business_type', 'created_at')
    search_fields = (
        'id',
        'application_ref',
        'tracking_number',
        'full_name',
        'email',
        'whatsapp_number',
        'city',
        'business_name',
        'cac_number',
        'reference_id',
    )
    readonly_fields = ('id', 'reference_id', 'created_at', 'updated_at', 'ip_address', 'user_agent')
    actions = ('mark_as_contacted', 'mark_as_approved', 'mark_as_dispatched', 'mark_as_archived')


    fieldsets = (
        ('Lead Information', {
            'fields': (
                'full_name',
                'email',
                'whatsapp_number',
                'interest',
                'status',
                'consent',
            )
        }),
        ('Business & Onboarding Details', {
            'fields': (
                'business_name',
                'business_type',
                'cac_number',
                'sector',
                'application_ref',
            )
        }),
        ('POS Hardware & Logistics', {
            'fields': (
                'pos_model',
                'terminal_count',
                'tracking_number',
                'street_address',
                'city',
                'state',
            )
        }),
        ('Settlement Account', {
            'fields': (
                'settlement_type',
                'settlement_bank',
                'settlement_account_number',
                'settlement_account_name',
            )
        }),
        ('Audit & System Metadata', {
            'classes': ('collapse',),
            'fields': (
                'notes',
                'source',
                'metadata',
                'reference_id',
                'ip_address',
                'user_agent',
                'created_at',
                'updated_at',
            )
        }),
    )

    @admin.action(description='Mark selected leads as Contacted')
    def mark_as_contacted(self, request, queryset):
        queryset.update(status='contacted')

    @admin.action(description='Mark selected leads as Approved')
    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Mark selected leads as Dispatched (POS Terminal)')
    def mark_as_dispatched(self, request, queryset):
        queryset.update(status='dispatched')

    @admin.action(description='Mark selected leads as Archived')
    def mark_as_archived(self, request, queryset):
        queryset.update(status='archived')

