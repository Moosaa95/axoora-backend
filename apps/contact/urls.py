from django.urls import path
from .views import ContactSubmitView, ContactInquiryListView, ContactInquiryDetailView

urlpatterns = [
    path('submit/', ContactSubmitView.as_view(), name='contact-submit'),
    path('inquiries/', ContactInquiryListView.as_view(), name='admin-inquiries-list'),
    path('inquiries/<uuid:inquiry_id>/', ContactInquiryDetailView.as_view(), name='admin-inquiries-detail'),
]
