"""
Admin configuration for booking_pages app.
"""

from django.contrib import admin

from .models import BookingPage, EmbedWidget


@admin.register(BookingPage)
class BookingPageAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "title",
        "primary_color",
        "custom_domain",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "show_powered_by", "font_family"]
    search_fields = ["user__email", "title", "custom_domain"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EmbedWidget)
class EmbedWidgetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "event_type",
        "embed_type",
        "total_views",
        "total_bookings",
        "is_active",
    ]
    list_filter = ["embed_type", "is_active"]
    search_fields = ["name", "user__email", "embed_token"]
    readonly_fields = ["embed_token", "total_views", "total_bookings", "created_at"]
