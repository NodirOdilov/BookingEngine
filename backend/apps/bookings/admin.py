"""
Admin configuration for bookings app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, BookingNote, BookingReminder, RescheduleHistory


class BookingNoteInline(admin.TabularInline):
    model = BookingNote
    extra = 0
    readonly_fields = ["created_at"]


class RescheduleHistoryInline(admin.TabularInline):
    model = RescheduleHistory
    extra = 0
    readonly_fields = ["created_at"]


class BookingReminderInline(admin.TabularInline):
    model = BookingReminder
    extra = 0
    readonly_fields = ["sent_at", "is_sent"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "invitee_name",
        "invitee_email",
        "host_display",
        "event_type",
        "start_time",
        "duration",
        "status_badge",
        "payment_status",
        "created_at",
    ]
    list_filter = [
        "status",
        "payment_status",
        "is_paid",
        "source",
        "location_type",
        "created_at",
    ]
    search_fields = [
        "reference",
        "invitee_name",
        "invitee_email",
        "host__email",
        "host__first_name",
        "host__last_name",
    ]
    readonly_fields = [
        "reference",
        "confirmed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "start_time"
    inlines = [BookingNoteInline, RescheduleHistoryInline, BookingReminderInline]

    fieldsets = (
        ("Booking Info", {
            "fields": (
                "reference",
                "event_type",
                "calendar",
                "status",
                "source",
            )
        }),
        ("Participants", {
            "fields": (
                "host",
                "invitee",
                "invitee_name",
                "invitee_email",
                "invitee_phone",
                "invitee_timezone",
                "invitee_notes",
            )
        }),
        ("Scheduling", {
            "fields": (
                "start_time",
                "end_time",
                "duration",
            )
        }),
        ("Location", {
            "fields": (
                "location_type",
                "location_detail",
                "meeting_link",
            )
        }),
        ("Payment", {
            "fields": (
                "is_paid",
                "payment_amount",
                "payment_currency",
                "payment_status",
                "stripe_payment_intent_id",
            )
        }),
        ("Cancellation", {
            "fields": (
                "cancellation_reason",
                "cancellation_notes",
                "cancelled_at",
            ),
            "classes": ("collapse",),
        }),
        ("Tracking", {
            "fields": (
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "google_event_id",
                "outlook_event_id",
                "custom_responses",
            ),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": (
                "confirmed_at",
                "created_at",
                "updated_at",
            ),
        }),
    )

    def host_display(self, obj):
        return obj.host.full_name or obj.host.email
    host_display.short_description = "Host"

    def status_badge(self, obj):
        colors = {
            "pending": "#F59E0B",
            "confirmed": "#10B981",
            "cancelled": "#EF4444",
            "completed": "#3B82F6",
            "no_show": "#6B7280",
            "rescheduled": "#8B5CF6",
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="padding:3px 8px;border-radius:4px;background:{};color:white;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"


@admin.register(BookingNote)
class BookingNoteAdmin(admin.ModelAdmin):
    list_display = ["booking", "author", "is_internal", "created_at"]
    list_filter = ["is_internal"]
    search_fields = ["booking__reference", "content"]


@admin.register(BookingReminder)
class BookingReminderAdmin(admin.ModelAdmin):
    list_display = [
        "booking",
        "reminder_type",
        "recipient",
        "minutes_before",
        "scheduled_at",
        "is_sent",
    ]
    list_filter = ["reminder_type", "is_sent", "recipient"]
    search_fields = ["booking__reference"]
