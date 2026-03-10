"""
Views for calendars app: calendar CRUD, availability rules, blocked times, available slots.
"""

from datetime import date, timedelta

from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AvailabilityRule, BlockedTime, Calendar, TimeSlot
from .serializers import (
    AvailabilityRuleCreateSerializer,
    AvailabilityRuleSerializer,
    AvailableSlotsQuerySerializer,
    BlockedTimeSerializer,
    BulkAvailabilitySerializer,
    CalendarCreateSerializer,
    CalendarSerializer,
    TimeSlotSerializer,
)
from .services import AvailabilityService


class CalendarViewSet(viewsets.ModelViewSet):
    """CRUD operations for user calendars."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CalendarCreateSerializer
        return CalendarSerializer

    def get_queryset(self):
        return Calendar.objects.filter(
            user=self.request.user
        ).select_related("user")

    def perform_create(self, serializer):
        # If this is the first calendar, make it the default
        is_first = not Calendar.objects.filter(user=self.request.user).exists()
        serializer.save(
            user=self.request.user,
            is_default=is_first or serializer.validated_data.get("is_default", False),
        )

    # ------------------------------------------------------------------
    # Availability rules nested under calendar
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get", "post"], url_path="availability-rules")
    def availability_rules(self, request, pk=None):
        """List or create availability rules for a calendar."""
        calendar = self.get_object()

        if request.method == "GET":
            rules = AvailabilityRule.objects.filter(calendar=calendar)
            serializer = AvailabilityRuleSerializer(rules, many=True)
            return Response(serializer.data)

        # POST - create new rule
        serializer = AvailabilityRuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(calendar=calendar)
        return Response(
            AvailabilityRuleSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="bulk-availability")
    def bulk_availability(self, request, pk=None):
        """
        Set the entire weekly availability schedule at once.
        Replaces all existing weekly rules for this calendar.
        """
        calendar = self.get_object()
        serializer = BulkAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Delete existing weekly rules
        AvailabilityRule.objects.filter(
            calendar=calendar,
            rule_type="weekly",
        ).delete()

        # Create new rules
        created_rules = []
        for rule_data in serializer.validated_data["rules"]:
            rule = AvailabilityRule.objects.create(
                calendar=calendar,
                **rule_data,
            )
            created_rules.append(rule)

        return Response(
            AvailabilityRuleSerializer(created_rules, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # Blocked times
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get", "post"], url_path="blocked-times")
    def blocked_times(self, request, pk=None):
        """List or create blocked time periods."""
        calendar = self.get_object()

        if request.method == "GET":
            blocked = BlockedTime.objects.filter(calendar=calendar)
            serializer = BlockedTimeSerializer(blocked, many=True)
            return Response(serializer.data)

        serializer = BlockedTimeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(calendar=calendar)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Available slots
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="available-slots")
    def available_slots(self, request, pk=None):
        """
        Get available time slots for a specific date.
        Query params: date (YYYY-MM-DD), timezone, duration (minutes).
        """
        calendar = self.get_object()
        query_serializer = AvailableSlotsQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        params = query_serializer.validated_data
        service = AvailabilityService(calendar)

        slots = service.get_available_slots(
            target_date=params["date"],
            duration_minutes=params.get("duration", 30),
            invitee_tz=params.get("timezone", "UTC"),
            event_type_id=params.get("event_type_id"),
        )

        return Response({
            "date": params["date"].isoformat(),
            "timezone": params.get("timezone", "UTC"),
            "duration_minutes": params.get("duration", 30),
            "slots": slots,
            "count": len(slots),
        })

    @action(detail=True, methods=["get"], url_path="available-dates")
    def available_dates(self, request, pk=None):
        """
        Get dates that have available slots within a range.
        Query params: start_date, end_date, duration.
        """
        calendar = self.get_object()

        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")
        duration = int(request.query_params.get("duration", 30))

        if not start_str:
            start_date = timezone.now().date()
        else:
            start_date = date.fromisoformat(start_str)

        if not end_str:
            end_date = start_date + timedelta(days=calendar.max_days_ahead)
        else:
            end_date = date.fromisoformat(end_str)

        service = AvailabilityService(calendar)
        available = service.get_available_dates(start_date, end_date, duration)

        return Response({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "available_dates": [d.isoformat() for d in available],
            "count": len(available),
        })


class AvailabilityRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a single availability rule."""

    serializer_class = AvailabilityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AvailabilityRule.objects.filter(
            calendar__user=self.request.user
        )


class BlockedTimeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a blocked time period."""

    serializer_class = BlockedTimeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlockedTime.objects.filter(
            calendar__user=self.request.user
        )
