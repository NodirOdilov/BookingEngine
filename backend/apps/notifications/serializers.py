"""
Serializers for notifications app.
"""

from rest_framework import serializers

from .models import NotificationLog, NotificationTemplate, UserNotificationPreference


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates."""

    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "template_type",
            "recipient_type",
            "name",
            "subject",
            "body_html",
            "body_text",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_default", "created_at", "updated_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs."""

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "channel",
            "notification_type",
            "recipient_email",
            "recipient_name",
            "subject",
            "body_preview",
            "status",
            "error_message",
            "sent_at",
            "delivered_at",
            "created_at",
        ]


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences."""

    class Meta:
        model = UserNotificationPreference
        fields = [
            "email_new_booking",
            "email_booking_cancelled",
            "email_booking_rescheduled",
            "email_booking_reminder",
            "email_daily_digest",
            "email_payment_received",
            "email_marketing",
            "sms_new_booking",
            "sms_booking_cancelled",
            "sms_booking_reminder",
            "push_new_booking",
            "push_booking_cancelled",
            "push_booking_reminder",
            "digest_time",
        ]
