from django.contrib import admin
from .models import ContactInquiry


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'category', 'email', 'phone', 'subject', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address')
    actions = ('mark_as_in_review', 'mark_as_resolved')


    @admin.action(description='Mark selected inquiries as In Review')
    def mark_as_in_review(self, request, queryset):
        queryset.update(status='in_review')

    @admin.action(description='Mark selected inquiries as Resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')
