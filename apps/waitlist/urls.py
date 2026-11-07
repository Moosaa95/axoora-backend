from django.urls import path
from .views import (
    WaitlistSubmitView,
    WaitlistLeadListView,
    WaitlistLeadDetailView,
    WaitlistTrackView,
)

urlpatterns = [
    path('submit/', WaitlistSubmitView.as_view(), name='waitlist-submit'),
    path('track/<str:tracking_code>/', WaitlistTrackView.as_view(), name='waitlist-track'),
    path('leads/', WaitlistLeadListView.as_view(), name='admin-leads-list'),
    path('leads/<uuid:lead_id>/', WaitlistLeadDetailView.as_view(), name='admin-leads-detail'),
]

