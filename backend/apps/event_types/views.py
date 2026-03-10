"""
Views for event_types app: CRUD for event types, public listing, location management.
"""

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EventType, EventTypeSettings, Location
from .serializers import (
    EventTypeCreateSerializer,
    EventTypePublicSerializer,
    EventTypeSerializer,
    EventTypeSettingsSerializer,
    LocationSerializer,
)


class EventTypeViewSet(viewsets.ModelViewSet):
    """CRUD operations for event types belonging to the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EventTypeCreateSerializer
        return EventTypeSerializer

    def get_queryset(self):
        return EventType.objects.filter(
            user=self.request.user
        ).select_related("calendar", "user", "organization").prefetch_related(
            "locations", "team_members"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get", "put", "patch"])
    def settings(self, request, pk=None):
        """Retrieve or update event type settings."""
        event_type = self.get_object()
        settings_obj, created = EventTypeSettings.objects.get_or_create(
            event_type=event_type
        )

        if request.method == "GET":
            serializer = EventTypeSettingsSerializer(settings_obj)
            return Response(serializer.data)

        serializer = EventTypeSettingsSerializer(
            settings_obj,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="locations")
    def locations(self, request, pk=None):
        """List or add locations to an event type."""
        event_type = self.get_object()

        if request.method == "GET":
            locations = Location.objects.filter(event_type=event_type)
            serializer = LocationSerializer(locations, many=True)
            return Response(serializer.data)

        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event_type=event_type)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Create a copy of an event type."""
        original = self.get_object()

        new_event = EventType.objects.create(
            user=request.user,
            calendar=original.calendar,
            organization=original.organization,
            name=f"{original.name} (Copy)",
            slug="",
            description=original.description,
            instructions=original.instructions,
            color=original.color,
            duration=original.duration,
            scheduling_type=original.scheduling_type,
            max_participants=original.max_participants,
            is_paid=original.is_paid,
            price=original.price,
            currency=original.currency,
            buffer_before=original.buffer_before,
            buffer_after=original.buffer_after,
            minimum_notice=original.minimum_notice,
            custom_questions=original.custom_questions,
            requires_confirmation=original.requires_confirmation,
            is_active=False,
        )

        # Copy locations
        for loc in original.locations.all():
            Location.objects.create(
                event_type=new_event,
                location_type=loc.location_type,
                address=loc.address,
                phone_number=loc.phone_number,
                additional_info=loc.additional_info,
                position=loc.position,
                is_default=loc.is_default,
            )

        # Copy settings
        if hasattr(original, "settings"):
            old_settings = original.settings
            EventTypeSettings.objects.create(
                event_type=new_event,
                email_reminder_enabled=old_settings.email_reminder_enabled,
                email_reminder_minutes=old_settings.email_reminder_minutes,
                sms_reminder_enabled=old_settings.sms_reminder_enabled,
                sms_reminder_minutes=old_settings.sms_reminder_minutes,
                follow_up_enabled=old_settings.follow_up_enabled,
                follow_up_delay_hours=old_settings.follow_up_delay_hours,
                max_events_per_day=old_settings.max_events_per_day,
                rolling_days_window=old_settings.rolling_days_window,
                slot_interval=old_settings.slot_interval,
                show_remaining_slots=old_settings.show_remaining_slots,
                allow_cancellation=old_settings.allow_cancellation,
                allow_rescheduling=old_settings.allow_rescheduling,
                cancellation_notice_hours=old_settings.cancellation_notice_hours,
            )

        return Response(
            EventTypeSerializer(new_event).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        """Toggle the active state of an event type."""
        event_type = self.get_object()
        event_type.is_active = not event_type.is_active
        event_type.save(update_fields=["is_active", "updated_at"])
        return Response({"is_active": event_type.is_active})


class PublicEventTypeListView(generics.ListAPIView):
    """
    Public endpoint listing active event types for a user's booking page.
    Looked up by user slug.
    """

    serializer_class = EventTypePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_slug = self.kwargs["user_slug"]
        return EventType.objects.filter(
            user__slug=user_slug,
            is_active=True,
            is_secret=False,
        ).select_related("user").prefetch_related("locations")


class PublicEventTypeDetailView(generics.RetrieveAPIView):
    """
    Public endpoint for a specific event type detail.
    Used on the booking page to show event type info before scheduling.
    """

    serializer_class = EventTypePublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        user_slug = self.kwargs["user_slug"]
        return EventType.objects.filter(
            user__slug=user_slug,
            is_active=True,
        ).select_related("user").prefetch_related("locations")
