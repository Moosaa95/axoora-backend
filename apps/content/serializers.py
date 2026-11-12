from rest_framework import serializers
from .enums import ArticleCategory, FaqCategory, ProductCategory, ProductStatus


class HeroConfigurationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    headline_business = serializers.CharField(max_length=255)
    subheadline_business = serializers.CharField()
    headline_personal = serializers.CharField(max_length=255)
    subheadline_personal = serializers.CharField()
    announcement_ticker = serializers.CharField(max_length=255)
    announcement_active = serializers.BooleanField()
    cta_text_primary = serializers.CharField(max_length=100)
    cta_text_secondary = serializers.CharField(max_length=100)
    trust_line = serializers.CharField(max_length=255)
    onboarding_steps = serializers.JSONField(required=False, default=list)
    updated_at = serializers.DateTimeField(read_only=True)


class JournalArticleSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    slug = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(choices=ArticleCategory.choices)
    title = serializers.CharField(max_length=255)
    summary = serializers.CharField()
    content = serializers.CharField(allow_blank=True, default='')
    read_time = serializers.CharField(max_length=50)
    author = serializers.CharField(max_length=120)
    published_date = serializers.CharField(max_length=50)
    is_published = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class JournalArticleCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=50, required=False, default='Engineering')
    summary = serializers.CharField()
    content = serializers.CharField(required=False, allow_blank=True, default='')
    read_time = serializers.CharField(max_length=50, required=False, default='4 min read')
    author = serializers.CharField(max_length=120, required=False, default='Axoora Editorial Board')
    published_date = serializers.CharField(max_length=50, required=False, default='Oct 2026')
    is_published = serializers.BooleanField(required=False, default=True)
    slug = serializers.CharField(max_length=255, required=False, allow_blank=True)



class FaqItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    question = serializers.CharField(max_length=300)
    answer = serializers.CharField()
    category = serializers.CharField(max_length=50)
    order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class FaqItemCreateUpdateSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=300, required=False)
    answer = serializers.CharField(required=False)
    category = serializers.CharField(max_length=50, required=False, default='General')
    order = serializers.IntegerField(required=False, default=0)
    is_active = serializers.BooleanField(required=False, default=True)


class MerchantStorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=120)
    role = serializers.CharField(max_length=120)
    location = serializers.CharField(max_length=120)
    quote = serializers.CharField()
    stat_label = serializers.CharField(max_length=100)
    stat_value = serializers.CharField(max_length=50)
    badge = serializers.CharField(max_length=100)
    accent_color = serializers.CharField(max_length=20)
    image_url = serializers.CharField(allow_blank=True, default='')
    featured = serializers.BooleanField()
    order = serializers.IntegerField()


class ProductItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=120)
    category = serializers.ChoiceField(choices=ProductCategory.choices)
    headline = serializers.CharField(max_length=255)
    fee_structure = serializers.CharField(max_length=120)
    status = serializers.ChoiceField(choices=ProductStatus.choices)
    highlight = serializers.CharField(max_length=120)
    description = serializers.CharField()
    order = serializers.IntegerField()
