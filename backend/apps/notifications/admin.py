"""
Admin configuration for notifications app.
"""

from django.contrib import admin

from .models import NotificationLog, NotificationTemplate, UserNotificationPreference


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "template_type",
        "recipient_type",
        "is_default",
        "is_active",
        "updated_at",
    ]
    list_filter = ["template_type", "recipient_type", "is_default", "is_active"]
    search_fields = ["name", "subject"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "notification_type",
        "channel",
        "recipient_email",
        "subject",
        "status",
        "sent_at",
        "created_at",
    ]
    list_filter = ["channel", "status", "notification_type", "created_at"]
    search_fields = ["recipient_email", "subject", "booking__reference"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "email_new_booking",
        "email_daily_digest",
        "sms_new_booking",
        "push_new_booking",
    ]
    search_fields = ["user__email"]
