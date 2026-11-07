from typing import Any, cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..common.pagination import paginate_queryset
from .models import HeroConfiguration, JournalArticle, FaqItem, MerchantStory, ProductItem
from .serializers import (
    HeroConfigurationSerializer,
    JournalArticleSerializer,
    JournalArticleCreateUpdateSerializer,
    FaqItemSerializer,
    MerchantStorySerializer,
    ProductItemSerializer,
)


class ContentBootstrapView(APIView):
    """
    Unified single-request bootstrap endpoint returning hero configuration, onboarding steps,
    merchant stories, products catalog, and journal articles in one round-trip.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        include_drafts = request.query_params.get('include_drafts', 'true').lower() in ('true', '1')
        hero = HeroConfiguration.get_or_create_config()
        stories = MerchantStory.get_all(featured_only=False)
        products = ProductItem.get_all()
        articles = JournalArticle.get_all(include_drafts=include_drafts)
        return Response({
            "hero": HeroConfigurationSerializer(hero).data,
            "stories": MerchantStorySerializer(stories, many=True).data,
            "products": ProductItemSerializer(products, many=True).data,
            "articles": JournalArticleSerializer(articles, many=True).data,
        })


class HeroConfigurationView(APIView):
    """
    Get or update the active hero banner configuration and announcement ticker.
    Uses model classmethods on HeroConfiguration.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        config = HeroConfiguration.get_or_create_config()
        return Response(HeroConfigurationSerializer(config).data)

    def put(self, request):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        config = HeroConfiguration.update_config(**data)
        return Response(HeroConfigurationSerializer(config).data)


class JournalArticleListView(APIView):
    """
    List published journal & news articles or create new ones.
    Uses model classmethods on JournalArticle.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        include_drafts = request.query_params.get('include_drafts', 'false').lower() in ('true', '1')

        queryset = JournalArticle.get_all(
            category=category,
            search=search,
            include_drafts=include_drafts,
        )

        paginator, page = paginate_queryset(queryset, request)
        serializer = JournalArticleSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = JournalArticleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        article = JournalArticle.create_article(
            title=data['title'],
            summary=data['summary'],
            category=data.get('category', 'Engineering'),
            content=data.get('content', ''),
            author=data.get('author', 'Axoora Editorial Board'),
            read_time=data.get('read_time', '4 min read'),
            published_date=data.get('published_date', 'Oct 2026'),
            is_published=data.get('is_published', True),
            slug=data.get('slug'),
        )

        return Response(
            {
                "success": True,
                "message": f"Article '{article.title}' published successfully.",
                "data": JournalArticleSerializer(article).data,
            },
            status=status.HTTP_201_CREATED,
        )


class JournalArticleDetailView(APIView):
    """
    Retrieve, update or delete a journal / news article by slug or UUID.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        include_drafts = request.query_params.get('include_drafts', 'true').lower() in ('true', '1')
        article = JournalArticle.get_by_id_or_slug(slug, include_drafts=include_drafts)
        if not article:
            return Response({"error": "Article not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(JournalArticleSerializer(article).data)

    def patch(self, request, slug):
        serializer = JournalArticleCreateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        updated = JournalArticle.update_article(slug, **data)
        if not updated:
            return Response({"error": "Article not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "message": f"Article '{updated.title}' updated successfully.",
            "data": JournalArticleSerializer(updated).data,
        })

    def delete(self, request, slug):
        deleted = JournalArticle.delete_article(slug)
        if not deleted:
            return Response({"error": "Article not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Article deleted successfully."})



class FaqItemListView(APIView):
    """
    List active resolution desk FAQs with optional category and search filters.
    Uses model classmethod FaqItem.get_active_faqs().
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        queryset = FaqItem.get_active_faqs(category=category, search=search)

        paginator, page = paginate_queryset(queryset, request, page_size=50)
        serializer = FaqItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MerchantStoryListView(APIView):
    """
    List customer and merchant impact stories or create a new one.
    Uses model classmethods on MerchantStory.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        featured_param = request.query_params.get('featured')
        featured_only = featured_param.lower() in ('true', '1') if featured_param else False
        queryset = MerchantStory.get_all(featured_only=featured_only)

        paginator, page = paginate_queryset(queryset, request, page_size=20)
        serializer = MerchantStorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        story = MerchantStory.create_story(**data)
        return Response(
            {
                "success": True,
                "data": MerchantStorySerializer(story).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MerchantStoryDetailView(APIView):
    """
    Update or delete a merchant story by UUID.
    """
    permission_classes = [permissions.AllowAny]

    def patch(self, request, story_id):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        updated = MerchantStory.update_story(story_id, **data)
        if not updated:
            return Response({"error": "Merchant story not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": MerchantStorySerializer(updated).data})

    def delete(self, request, story_id):
        deleted = MerchantStory.delete_story(story_id)
        if not deleted:
            return Response({"error": "Merchant story not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Merchant story deleted."})


class ProductItemListView(APIView):
    """
    List Axoora products catalog or create a new product.
    Uses model classmethods on ProductItem.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category')
        prod_status = request.query_params.get('status')
        queryset = ProductItem.get_all(category=category, status=prod_status)

        paginator, page = paginate_queryset(queryset, request, page_size=20)
        serializer = ProductItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        product = ProductItem.create_product(**data)
        return Response(
            {
                "success": True,
                "data": ProductItemSerializer(product).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProductItemDetailView(APIView):
    """
    Update or delete a product item by UUID.
    """
    permission_classes = [permissions.AllowAny]

    def patch(self, request, product_id):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        updated = ProductItem.update_product(product_id, **data)
        if not updated:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": ProductItemSerializer(updated).data})

    def delete(self, request, product_id):
        deleted = ProductItem.delete_product(product_id)
        if not deleted:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Product deleted."})
