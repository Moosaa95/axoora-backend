from django.contrib import admin
from django.utils.html import format_html
from .models import ChatSession, ChatMessage, ChatKnowledgeRule, KnowledgeDocument, KnowledgeChunk


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'text', 'is_escalation_trigger', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return True


class KnowledgeChunkInline(admin.TabularInline):
    model = KnowledgeChunk
    extra = 0
    fields = ('chunk_title', 'content', 'keywords')
    readonly_fields = ('created_at',)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_code',
        'customer_name_display',
        'customer_phone',
        'status_badge',
        'message_count',
        'escalated_at',
        'created_at',
    )
    list_filter = ('status', 'created_at', 'escalated_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_email', 'escalation_reason', 'id')
    readonly_fields = ('id', 'session_id', 'ticket_code', 'ip_address', 'user_agent', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]
    actions = ('mark_as_human_active', 'mark_as_resolved', 'mark_as_closed')

    @admin.display(description='Customer')
    def customer_name_display(self, obj):
        return obj.customer_name or format_html("<span style='color: #888;'>Guest User</span>")

    @admin.display(description='Messages')
    def message_count(self, obj):
        return obj.messages.count()

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'ai_active': '#3B82F6',       # Blue
            'escalated': '#EF4444',       # Red alert
            'human_active': '#F59E0B',     # Amber
            'resolved': '#10B981',        # Green
            'closed': '#6B7280',          # Grey
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 9999px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.action(description='Take over as Human Agent (Mark Human Active)')
    def mark_as_human_active(self, request, queryset):
        queryset.update(status='human_active', assigned_agent=request.user)

    @admin.action(description='Mark selected chats as Resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')

    @admin.action(description='Mark selected chats as Closed')
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')


@admin.register(ChatKnowledgeRule)
class ChatKnowledgeRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'keywords', 'priority', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'keywords', 'response_text')
    list_editable = ('priority', 'is_active')


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'chunks_count', 'updated_at')
    list_filter = ('category', 'is_active', 'updated_at')
    search_fields = ('title', 'content', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [KnowledgeChunkInline]

    @admin.display(description='Indexed Chunks')
    def chunks_count(self, obj):
        return obj.chunks.count()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Automatically update/create chunks for this document
        obj.chunks.all().delete()
        sections = [s.strip() for s in obj.content.split('\n') if s.strip()]
        for idx, sec in enumerate(sections):
            KnowledgeChunk.objects.create(
                document=obj,
                chunk_title=f"{obj.title} (Part {idx + 1})",
                content=f"{obj.title}: {sec}",
                keywords=f"{obj.category}, {obj.title}, {sec[:50]}",
                source_type='document',
                source_id=f"{obj.slug}-{idx}",
            )


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ('chunk_title', 'source_type', 'source_id', 'has_embedding', 'created_at')
    list_filter = ('source_type', 'created_at')
    search_fields = ('chunk_title', 'content', 'keywords')


    @admin.display(boolean=True, description='Vector Embedded')
    def has_embedding(self, obj):
        return bool(obj.embedding)
