"""
Serializers for event types app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer
from .models import EventType, EventTypeSettings, Location


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for event type locations."""

    location_type_display = serializers.CharField(
        source="get_location_type_display", read_only=True
    )

    class Meta:
        model = Location
        fields = [
            "id",
            "location_type",
            "location_type_display",
            "address",
            "phone_number",
            "additional_info",
            "position",
            "is_default",
        ]
        read_only_fields = ["id"]


class EventTypeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for event type extended settings."""

    class Meta:
        model = EventTypeSettings
        fields = [
            "id",
            "email_reminder_enabled",
            "email_reminder_minutes",
            "sms_reminder_enabled",
            "sms_reminder_minutes",
            "follow_up_enabled",
            "follow_up_delay_hours",
            "max_events_per_day",
            "rolling_days_window",
            "slot_interval",
            "show_remaining_slots",
            "allow_cancellation",
            "allow_rescheduling",
            "cancellation_notice_hours",
        ]
        read_only_fields = ["id"]


class EventTypeSerializer(serializers.ModelSerializer):
    """Full event type serializer with nested locations and settings."""

    user = UserMinimalSerializer(read_only=True)
    locations = LocationSerializer(many=True, read_only=True)
    settings = EventTypeSettingsSerializer(read_only=True)
    effective_buffer_before = serializers.ReadOnlyField()
    effective_buffer_after = serializers.ReadOnlyField()
    effective_minimum_notice = serializers.ReadOnlyField()
    booking_url = serializers.SerializerMethodField()

    class Meta:
        model = EventType
        fields = [
            "id",
            "user",
            "calendar",
            "organization",
            "name",
            "slug",
            "description",
            "instructions",
            "color",
            "duration",
            "scheduling_type",
            "max_participants",
            "is_paid",
            "price",
            "currency",
            "buffer_before",
            "buffer_after",
            "minimum_notice",
            "max_bookings_per_day",
            "effective_buffer_before",
            "effective_buffer_after",
            "effective_minimum_notice",
            "custom_questions",
            "requires_confirmation",
            "confirmation_redirect_url",
            "is_active",
            "is_secret",
            "locations",
            "settings",
            "booking_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_booking_url(self, obj):
        return f"/p/{obj.user.slug}/{obj.slug}"


class EventTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating event types."""

    locations = LocationSerializer(many=True, required=False)
    settings = EventTypeSettingsSerializer(required=False)

    class Meta:
        model = EventType
        fields = [
            "calendar",
            "organization",
            "name",
            "description",
            "instructions",
            "color",
            "duration",
            "scheduling_type",
            "max_participants",
            "is_paid",
            "price",
            "currency",
            "buffer_before",
            "buffer_after",
            "minimum_notice",
            "max_bookings_per_day",
            "custom_questions",
            "requires_confirmation",
            "confirmation_redirect_url",
            "is_active",
            "is_secret",
            "locations",
            "settings",
        ]

    def validate_calendar(self, value):
        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError(
                "You can only create event types on your own calendars."
            )
        return value

    def create(self, validated_data):
        locations_data = validated_data.pop("locations", [])
        settings_data = validated_data.pop("settings", {})

        event_type = EventType.objects.create(**validated_data)

        # Create locations
        for position, loc_data in enumerate(locations_data):
            Location.objects.create(
                event_type=event_type,
                position=position,
                **loc_data,
            )

        # Create settings
        EventTypeSettings.objects.create(
            event_type=event_type,
            **settings_data,
        )

        return event_type

    def update(self, instance, validated_data):
        locations_data = validated_data.pop("locations", None)
        settings_data = validated_data.pop("settings", None)

        # Update event type fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update locations if provided
        if locations_data is not None:
            instance.locations.all().delete()
            for position, loc_data in enumerate(locations_data):
                Location.objects.create(
                    event_type=instance,
                    position=position,
                    **loc_data,
                )

        # Update settings if provided
        if settings_data is not None:
            settings_obj, _ = EventTypeSettings.objects.get_or_create(
                event_type=instance
            )
            for attr, value in settings_data.items():
                setattr(settings_obj, attr, value)
            settings_obj.save()

        return instance


class EventTypePublicSerializer(serializers.ModelSerializer):
    """Public-facing event type serializer (for booking pages)."""

    user = UserMinimalSerializer(read_only=True)
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = EventType
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "instructions",
            "color",
            "duration",
            "scheduling_type",
            "max_participants",
            "is_paid",
            "price",
            "currency",
            "custom_questions",
            "user",
            "locations",
        ]
