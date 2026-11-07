from django.contrib import admin
from .models import HeroConfiguration, JournalArticle, FaqItem, MerchantStory, ProductItem


@admin.register(HeroConfiguration)
class HeroConfigurationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'headline_business', 'announcement_active', 'updated_at')


@admin.register(JournalArticle)
class JournalArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'published_date', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'summary', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(FaqItem)
class FaqItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')


@admin.register(MerchantStory)
class MerchantStoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'location', 'stat_value', 'stat_label', 'featured', 'order')
    list_filter = ('featured',)
    search_fields = ('name', 'role', 'location', 'quote')
    list_editable = ('featured', 'order')


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'fee_structure', 'order')
    list_filter = ('category', 'status')
    search_fields = ('name', 'headline', 'description')
    list_editable = ('order',)

