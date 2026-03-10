"""
Serializers for bookings app: booking creation, listing, rescheduling, cancellation.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer
from apps.calendars.services import check_slot_availability
from apps.event_types.serializers import EventTypeSerializer
from .models import Booking, BookingNote, BookingReminder, RescheduleHistory


class BookingNoteSerializer(serializers.ModelSerializer):
    """Serializer for booking notes."""

    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BookingNote
        fields = [
            "id",
            "booking",
            "author",
            "content",
            "is_internal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "booking", "author", "created_at", "updated_at"]


class RescheduleHistorySerializer(serializers.ModelSerializer):
    """Serializer for reschedule history entries."""

    class Meta:
        model = RescheduleHistory
        fields = [
            "id",
            "previous_start",
            "previous_end",
            "new_start",
            "new_end",
            "rescheduled_by_email",
            "reason",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BookingReminderSerializer(serializers.ModelSerializer):
    """Serializer for booking reminders."""

    class Meta:
        model = BookingReminder
        fields = [
            "id",
            "reminder_type",
            "recipient",
            "minutes_before",
            "scheduled_at",
            "sent_at",
            "is_sent",
        ]
        read_only_fields = ["id", "sent_at", "is_sent"]


class BookingSerializer(serializers.ModelSerializer):
    """Full booking serializer with nested relationships."""

    host = UserMinimalSerializer(read_only=True)
    event_type_detail = EventTypeSerializer(source="event_type", read_only=True)
    notes = BookingNoteSerializer(many=True, read_only=True)
    reschedule_history = RescheduleHistorySerializer(many=True, read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    can_reschedule = serializers.ReadOnlyField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "event_type",
            "event_type_detail",
            "calendar",
            "host",
            "invitee",
            "invitee_name",
            "invitee_email",
            "invitee_phone",
            "invitee_timezone",
            "invitee_notes",
            "custom_responses",
            "start_time",
            "end_time",
            "duration",
            "status",
            "confirmed_at",
            "cancelled_at",
            "cancellation_reason",
            "location_type",
            "location_detail",
            "meeting_link",
            "is_paid",
            "payment_amount",
            "payment_currency",
            "payment_status",
            "source",
            "is_upcoming",
            "is_past",
            "can_cancel",
            "can_reschedule",
            "notes",
            "reschedule_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "reference", "host", "confirmed_at",
            "cancelled_at", "created_at", "updated_at",
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight booking serializer for list views."""

    host_name = serializers.CharField(source="host.full_name", read_only=True)
    event_type_name = serializers.CharField(
        source="event_type.name", read_only=True, default=""
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "event_type_name",
            "host_name",
            "invitee_name",
            "invitee_email",
            "start_time",
            "end_time",
            "duration",
            "status",
            "location_type",
            "is_paid",
            "payment_status",
            "created_at",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a booking from a public booking page.
    Validates slot availability, applies event type rules, and sets up reminders.
    """

    class Meta:
        model = Booking
        fields = [
            "event_type",
            "start_time",
            "invitee_name",
            "invitee_email",
            "invitee_phone",
            "invitee_timezone",
            "invitee_notes",
            "custom_responses",
            "location_type",
            "location_detail",
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
        ]

    def validate_event_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This event type is not available.")
        return value

    def validate(self, attrs):
        event_type = attrs["event_type"]
        start_time = attrs["start_time"]
        duration = event_type.duration
        end_time = start_time + timedelta(minutes=duration)

        # Validate minimum notice
        notice_hours = event_type.effective_minimum_notice
        if start_time < timezone.now() + timedelta(hours=notice_hours):
            raise serializers.ValidationError({
                "start_time": f"Bookings require at least {notice_hours} hours notice."
            })

        # Validate max days ahead
        max_days = event_type.calendar.max_days_ahead
        if start_time.date() > (timezone.now() + timedelta(days=max_days)).date():
            raise serializers.ValidationError({
                "start_time": f"Bookings can only be made up to {max_days} days ahead."
            })

        # Validate slot availability
        if not check_slot_availability(event_type.calendar, start_time, end_time):
            raise serializers.ValidationError({
                "start_time": "This time slot is no longer available."
            })

        attrs["end_time"] = end_time
        attrs["duration"] = duration
        return attrs

    def create(self, validated_data):
        event_type = validated_data["event_type"]
        validated_data["calendar"] = event_type.calendar
        validated_data["host"] = event_type.user

        # Set payment info from event type
        if event_type.is_paid:
            validated_data["is_paid"] = True
            validated_data["payment_amount"] = event_type.price
            validated_data["payment_currency"] = event_type.currency
            validated_data["payment_status"] = "pending"

        # Auto-confirm if not requiring confirmation
        if not event_type.requires_confirmation:
            validated_data["status"] = "confirmed"
            validated_data["confirmed_at"] = timezone.now()

        booking = Booking.objects.create(**validated_data)

        # Create reminders based on event type settings
        self._create_reminders(booking, event_type)

        return booking

    def _create_reminders(self, booking, event_type):
        """Create reminder entries based on event type settings."""
        if not hasattr(event_type, "settings"):
            return

        settings = event_type.settings

        if settings.email_reminder_enabled and settings.email_reminder_minutes:
            for minutes in settings.email_reminder_minutes:
                scheduled = booking.start_time - timedelta(minutes=minutes)
                if scheduled > timezone.now():
                    BookingReminder.objects.create(
                        booking=booking,
                        reminder_type="email",
                        recipient="both",
                        minutes_before=minutes,
                        scheduled_at=scheduled,
                    )

        if settings.sms_reminder_enabled and settings.sms_reminder_minutes:
            for minutes in settings.sms_reminder_minutes:
                scheduled = booking.start_time - timedelta(minutes=minutes)
                if scheduled > timezone.now():
                    BookingReminder.objects.create(
                        booking=booking,
                        reminder_type="sms",
                        recipient="both",
                        minutes_before=minutes,
                        scheduled_at=scheduled,
                    )


class BookingRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling a booking."""

    new_start_time = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_new_start_time(self, value):
        booking = self.context["booking"]
        if value < timezone.now():
            raise serializers.ValidationError("Cannot reschedule to a time in the past.")

        end_time = value + timedelta(minutes=booking.duration)
        if not check_slot_availability(
            booking.calendar, value, end_time, exclude_booking_id=str(booking.id)
        ):
            raise serializers.ValidationError("The new time slot is not available.")

        return value


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for booking cancellation."""

    reason = serializers.ChoiceField(
        choices=Booking.CANCELLATION_REASON_CHOICES,
        default="other",
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class BookingPublicSerializer(serializers.ModelSerializer):
    """Public-facing booking serializer (for confirmation pages)."""

    event_type_name = serializers.CharField(
        source="event_type.name", read_only=True, default=""
    )
    host_name = serializers.CharField(source="host.full_name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "event_type_name",
            "host_name",
            "invitee_name",
            "invitee_email",
            "start_time",
            "end_time",
            "duration",
            "status",
            "location_type",
            "location_detail",
            "meeting_link",
            "can_cancel",
            "can_reschedule",
        ]
