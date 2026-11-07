from typing import Any, cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..common.pagination import paginate_queryset
from .models import ContactInquiry
from .serializers import ContactInquiryCreateSerializer, ContactInquiryDetailSerializer


class ContactSubmitView(APIView):
    """
    Public endpoint for contact inquiries and partnership pitches.
    Uses serializers.Serializer and calls ContactInquiry.create_inquiry() model classmethod.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactInquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

        # Model query via classmethod
        inquiry = ContactInquiry.create_inquiry(
            full_name=data['full_name'],
            email=data['email'],
            phone=data.get('phone', ''),
            category=data.get('category', 'general'),
            subject=data['subject'],
            message=data['message'],
            ip_address=ip_address,
        )

        return Response(
            {
                "success": True,
                "message": "Thank you for reaching out to Axoora. Our team will review your message promptly.",
                "id": inquiry.id,
                "data": ContactInquiryDetailSerializer(inquiry).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ContactInquiryListView(APIView):
    """
    Staff/Admin endpoint to view, search, and paginate inbound contact inquiries.
    Uses model classmethod ContactInquiry.get_all().
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get('status')
        category_filter = request.query_params.get('category')
        search_query = request.query_params.get('search')

        queryset = ContactInquiry.get_all(
            status=status_filter,
            category=category_filter,
            search=search_query,
        )

        paginator, page = paginate_queryset(queryset, request)
        serializer = ContactInquiryDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ContactInquiryDetailView(APIView):
    """
    Staff/Admin endpoint to inspect or update an individual inquiry.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, inquiry_id):
        inquiry = ContactInquiry.get_by_id(inquiry_id)
        if not inquiry:
            return Response({"error": "Inquiry not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ContactInquiryDetailSerializer(inquiry).data)

    def patch(self, request, inquiry_id):
        req_data: dict[str, Any] = cast(dict[str, Any], request.data)
        new_status = req_data.get('status')
        response_notes = req_data.get('response_notes')

        if not new_status and response_notes is None:
            return Response({"error": "No update fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        inquiry = ContactInquiry.update_status(
            inquiry_id,
            new_status=new_status,
            response_notes=response_notes,
        )
        if not inquiry:
            return Response({"error": "Inquiry not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "data": ContactInquiryDetailSerializer(inquiry).data,
        })
