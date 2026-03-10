"""
Admin configuration for integrations app.
"""

from django.contrib import admin

from .models import CalendarIntegration, WebhookEndpoint


@admin.register(CalendarIntegration)
class CalendarIntegrationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "provider",
        "provider_email",
        "sync_status",
        "sync_direction",
        "check_conflicts",
        "last_synced_at",
        "is_active",
    ]
    list_filter = ["provider", "sync_status", "is_active", "check_conflicts"]
    search_fields = ["user__email", "provider_email"]
    readonly_fields = ["created_at", "updated_at", "last_synced_at"]

    fieldsets = (
        (None, {
            "fields": ("user", "provider", "provider_email", "is_active")
        }),
        ("Sync Settings", {
            "fields": (
                "sync_status",
                "sync_direction",
                "external_calendar_id",
                "external_calendar_name",
                "check_conflicts",
            )
        }),
        ("Sync Status", {
            "fields": (
                "last_synced_at",
                "last_sync_error",
                "sync_token",
            ),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = [
        "url",
        "user",
        "is_active",
        "total_deliveries",
        "total_failures",
        "failure_rate",
        "last_delivery_at",
        "last_response_code",
    ]
    list_filter = ["is_active"]
    search_fields = ["url", "user__email", "description"]
    readonly_fields = [
        "total_deliveries", "total_failures",
        "last_delivery_at", "last_failure_at",
        "last_response_code", "created_at",
    ]
