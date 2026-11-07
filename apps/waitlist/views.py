from typing import Any, cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from ..common.pagination import paginate_queryset
from .models import WaitlistLead
from .serializers import WaitlistLeadCreateSerializer, WaitlistLeadDetailSerializer


class WaitlistSubmitView(APIView):
    """
    Public endpoint for users, merchants, and agents to submit waitlist / onboarding requests.
    Uses serializers.Serializer and calls WaitlistLead.create_lead() model classmethod.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = WaitlistLeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = cast(dict[str, Any], serializer.validated_data)


        # Capture IP address and User Agent
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Model query via classmethod
        lead = WaitlistLead.create_lead(
            full_name=data['full_name'],
            whatsapp_number=data['whatsapp_number'],
            email=data['email'],
            city=data.get('city', ''),
            state=data.get('state', ''),
            business_name=data.get('business_name', ''),
            interest=data.get('interest', 'business'),
            consent=data.get('consent', True),
            source=data.get('source', 'website'),
            notes=data.get('notes', ''),
            business_type=data.get('business_type', ''),
            cac_number=data.get('cac_number', ''),
            sector=data.get('sector', ''),
            pos_model=data.get('pos_model', ''),
            terminal_count=data.get('terminal_count', 1),
            street_address=data.get('street_address', ''),
            settlement_type=data.get('settlement_type', 'instant'),
            settlement_bank=data.get('settlement_bank', ''),
            settlement_account_number=data.get('settlement_account_number', ''),
            settlement_account_name=data.get('settlement_account_name', ''),
            application_ref=data.get('application_ref', ''),
            tracking_number=data.get('tracking_number', ''),
            metadata=data.get('metadata', {}),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return Response(
            {
                "success": True,
                "message": "You have been successfully added to the Axoora priority onboarding pipeline.",
                "reference_id": str(lead.reference_id),
                "application_ref": lead.application_ref,
                "tracking_number": lead.tracking_number,
                "data": WaitlistLeadDetailSerializer(lead).data,
            },
            status=status.HTTP_201_CREATED,
        )


class WaitlistTrackView(APIView):
    """
    Public lookup endpoint to track business application and POS terminal dispatch status.
    Lookup via application_ref or tracking_number.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, tracking_code):
        lead = WaitlistLead.get_by_ref_or_tracking(tracking_code)
        if not lead:
            return Response(
                {
                    "found": False,
                    "message": f"No application or shipment found matching '{tracking_code}'.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "found": True,
                "application_ref": lead.application_ref or str(lead.reference_id)[:8].upper(),
                "tracking_number": lead.tracking_number,
                "status": lead.status,
                "status_display": lead.get_status_display(),
                "business_name": lead.business_name or lead.full_name,
                "pos_model": lead.pos_model or 'Apex Smart Terminal',
                "terminal_count": lead.terminal_count,
                "city": lead.city,
                "state": lead.state,
                "submitted_at": lead.created_at,
                "updated_at": lead.updated_at,
            },
            status=status.HTTP_200_OK,
        )



class WaitlistLeadListView(APIView):
    """
    Staff/Admin endpoint to view, search, and paginate waitlist submissions.
    Uses model classmethod WaitlistLead.get_all().
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get('status')
        interest_filter = request.query_params.get('interest')
        search_query = request.query_params.get('search')

        # Model query via classmethod
        queryset = WaitlistLead.get_all(
            status=status_filter,
            interest=interest_filter,
            search=search_query,
        )

        paginator, page = paginate_queryset(queryset, request)
        serializer = WaitlistLeadDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class WaitlistLeadDetailView(APIView):
    """
    Staff/Admin endpoint to inspect, update status, or delete an individual lead.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, lead_id):
        lead = WaitlistLead.get_by_id(lead_id)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(WaitlistLeadDetailSerializer(lead).data)

    def patch(self, request, lead_id):
        data: dict[str, Any] = cast(dict[str, Any], request.data)
        new_status = data.get('status')
        notes = data.get('notes')

        if not new_status and notes is None:
            return Response({"error": "No update fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        lead = WaitlistLead.update_lead_status(lead_id, new_status=new_status, notes=notes)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)


        return Response({
            "success": True,
            "data": WaitlistLeadDetailSerializer(lead).data,
        })

    def delete(self, request, lead_id):
        deleted = WaitlistLead.delete_by_id(lead_id)
        if not deleted:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Lead deleted successfully."}, status=status.HTTP_200_OK)
