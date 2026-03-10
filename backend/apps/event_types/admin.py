"""
Admin configuration for event_types app.
"""

from django.contrib import admin

from .models import EventType, EventTypeSettings, Location


class LocationInline(admin.TabularInline):
    model = Location
    extra = 0


class EventTypeSettingsInline(admin.StackedInline):
    model = EventTypeSettings
    can_delete = False


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "calendar",
        "duration",
        "scheduling_type",
        "is_paid",
        "price",
        "is_active",
        "is_secret",
        "created_at",
    ]
    list_filter = [
        "scheduling_type",
        "is_active",
        "is_secret",
        "is_paid",
        "duration",
    ]
    search_fields = ["name", "slug", "user__email", "description"]
    readonly_fields = ["slug", "created_at", "updated_at"]
    inlines = [LocationInline, EventTypeSettingsInline]

    fieldsets = (
        (None, {
            "fields": (
                "user",
                "calendar",
                "organization",
                "name",
                "slug",
                "description",
                "instructions",
                "color",
            )
        }),
        ("Scheduling", {
            "fields": (
                "duration",
                "scheduling_type",
                "max_participants",
                "buffer_before",
                "buffer_after",
                "minimum_notice",
                "max_bookings_per_day",
            )
        }),
        ("Pricing", {
            "fields": ("is_paid", "price", "currency"),
        }),
        ("Booking Options", {
            "fields": (
                "custom_questions",
                "requires_confirmation",
                "confirmation_redirect_url",
                "is_active",
                "is_secret",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )
