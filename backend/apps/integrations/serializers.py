"""
Serializers for integrations app.
"""

from rest_framework import serializers

from .models import CalendarIntegration, WebhookEndpoint


class CalendarIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for calendar integrations (excludes tokens)."""

    provider_display = serializers.CharField(
        source="get_provider_display", read_only=True
    )
    is_token_expired = serializers.ReadOnlyField()

    class Meta:
        model = CalendarIntegration
        fields = [
            "id",
            "provider",
            "provider_display",
            "provider_email",
            "sync_status",
            "sync_direction",
            "external_calendar_id",
            "external_calendar_name",
            "check_conflicts",
            "last_synced_at",
            "last_sync_error",
            "is_token_expired",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id", "provider_email", "last_synced_at",
            "last_sync_error", "created_at",
        ]


class CalendarIntegrationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating calendar integration settings."""

    class Meta:
        model = CalendarIntegration
        fields = [
            "sync_direction",
            "external_calendar_id",
            "external_calendar_name",
            "check_conflicts",
            "is_active",
        ]


class WebhookEndpointSerializer(serializers.ModelSerializer):
    """Serializer for webhook endpoints."""

    failure_rate = serializers.ReadOnlyField()

    class Meta:
        model = WebhookEndpoint
        fields = [
            "id",
            "url",
            "secret",
            "events",
            "description",
            "is_active",
            "total_deliveries",
            "total_failures",
            "failure_rate",
            "last_delivery_at",
            "last_response_code",
            "created_at",
        ]
        read_only_fields = [
            "id", "total_deliveries", "total_failures",
            "last_delivery_at", "last_response_code", "created_at",
        ]
        extra_kwargs = {
            "secret": {"write_only": True},
        }


class WebhookEndpointCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating webhook endpoints."""

    class Meta:
        model = WebhookEndpoint
        fields = ["url", "secret", "events", "description"]

    def validate_events(self, value):
        valid_events = [choice[0] for choice in WebhookEndpoint.EVENT_CHOICES]
        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(
                    f"Invalid event type: {event}. "
                    f"Valid types: {', '.join(valid_events)}"
                )
        return value
