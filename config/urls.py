"""
URL configuration for Axoora Backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def api_root(request):
    return JsonResponse({
        "status": "healthy",
        "service": "Axoora Sovereign Fintech API",
        "version": "v1.0.0",
        "documentation": "/api/v1/",
        "endpoints": {
            "waitlist_submit": "/api/v1/waitlist/submit/",
            "waitlist_track": "/api/v1/waitlist/track/<tracking_code>/",
            "admin_leads": "/api/v1/waitlist/leads/",
            "content_hero": "/api/v1/content/hero/",
            "content_articles": "/api/v1/content/articles/",
            "content_faqs": "/api/v1/content/faqs/",
            "content_stories": "/api/v1/content/stories/",
            "content_products": "/api/v1/content/products/",
            "contact_submit": "/api/v1/contact/submit/",
            "admin_inquiries": "/api/v1/contact/inquiries/",
            "chat_send_message": "/api/v1/chat/message/",
            "chat_escalate_human": "/api/v1/chat/escalate/",
            "chat_history": "/api/v1/chat/history/<session_id>/",
            "chat_admin_sessions": "/api/v1/chat/sessions/",
            "auth_login": "/api/v1/team/auth/login/",
            "auth_me": "/api/v1/team/auth/me/",
            "auth_logout": "/api/v1/team/auth/logout/",
            "team_roles": "/api/v1/team/roles/",
            "team_members": "/api/v1/team/members/",
            "team_permissions": "/api/v1/team/permissions/",
            "django_admin": "/admin/",
        },
    })


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "database": "connected",
        "service": "axoora-backend",
    })


urlpatterns = [
    # API status root
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),

    # Django Admin
    path('admin/', admin.site.urls),

    # Axoora V1 API Routers
    path('api/v1/team/', include('apps.team.urls')),
    path('api/v1/waitlist/', include('apps.waitlist.urls')),
    path('api/v1/content/', include('apps.content.urls')),
    path('api/v1/contact/', include('apps.contact.urls')),
    path('api/v1/chat/', include('apps.chat.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
