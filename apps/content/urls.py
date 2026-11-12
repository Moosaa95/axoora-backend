from django.urls import path
from .views import (
    ContentBootstrapView,
    HeroConfigurationView,
    JournalArticleListView,
    JournalArticleDetailView,
    FaqItemListView,
    FaqItemDetailView,
    MerchantStoryListView,
    MerchantStoryDetailView,
    ProductItemListView,
    ProductItemDetailView,
)

urlpatterns = [
    path('bootstrap/', ContentBootstrapView.as_view(), name='content-bootstrap'),
    path('hero/', HeroConfigurationView.as_view(), name='hero-config'),
    path('articles/', JournalArticleListView.as_view(), name='journal-articles-list'),
    path('articles/<str:slug>/', JournalArticleDetailView.as_view(), name='journal-articles-detail'),
    path('faqs/', FaqItemListView.as_view(), name='faqs-list'),
    path('faqs/<str:faq_id>/', FaqItemDetailView.as_view(), name='faqs-detail'),
    path('stories/', MerchantStoryListView.as_view(), name='merchant-stories-list'),
    path('stories/<str:story_id>/', MerchantStoryDetailView.as_view(), name='merchant-stories-detail'),
    path('products/', ProductItemListView.as_view(), name='products-list'),
    path('products/<str:product_id>/', ProductItemDetailView.as_view(), name='products-detail'),
]
