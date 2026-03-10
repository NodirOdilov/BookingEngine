"""
Serializers for booking_pages app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer
from .models import BookingPage, EmbedWidget


class BookingPageSerializer(serializers.ModelSerializer):
    """Full booking page serializer."""

    user = UserMinimalSerializer(read_only=True)
    public_url = serializers.ReadOnlyField()

    class Meta:
        model = BookingPage
        fields = [
            "id",
            "user",
            "organization",
            "title",
            "subtitle",
            "welcome_message",
            "logo",
            "cover_image",
            "primary_color",
            "text_color",
            "background_color",
            "font_family",
            "meta_title",
            "meta_description",
            "show_powered_by",
            "show_avatar",
            "show_event_duration",
            "show_event_description",
            "show_timezone_selector",
            "custom_domain",
            "is_custom_domain_verified",
            "google_analytics_id",
            "facebook_pixel_id",
            "public_url",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "user", "is_custom_domain_verified",
            "created_at", "updated_at",
        ]


class BookingPageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating booking page branding."""

    class Meta:
        model = BookingPage
        fields = [
            "title",
            "subtitle",
            "welcome_message",
            "logo",
            "cover_image",
            "primary_color",
            "text_color",
            "background_color",
            "font_family",
            "meta_title",
            "meta_description",
            "show_powered_by",
            "show_avatar",
            "show_event_duration",
            "show_event_description",
            "show_timezone_selector",
            "google_analytics_id",
            "facebook_pixel_id",
        ]


class BookingPagePublicSerializer(serializers.ModelSerializer):
    """Public-facing booking page serializer."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BookingPage
        fields = [
            "title",
            "subtitle",
            "welcome_message",
            "logo",
            "cover_image",
            "primary_color",
            "text_color",
            "background_color",
            "font_family",
            "show_avatar",
            "show_event_duration",
            "show_event_description",
            "show_timezone_selector",
            "user",
        ]


class EmbedWidgetSerializer(serializers.ModelSerializer):
    """Full embed widget serializer."""

    embed_code = serializers.ReadOnlyField()

    class Meta:
        model = EmbedWidget
        fields = [
            "id",
            "event_type",
            "name",
            "embed_type",
            "embed_token",
            "button_text",
            "button_color",
            "button_text_color",
            "button_position",
            "width",
            "height",
            "total_views",
            "total_bookings",
            "embed_code",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id", "embed_token", "total_views",
            "total_bookings", "created_at",
        ]
