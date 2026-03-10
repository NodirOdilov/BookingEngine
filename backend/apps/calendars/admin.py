"""
Admin configuration for calendars app.
"""

from django.contrib import admin

from .models import AvailabilityRule, BlockedTime, Calendar, TimeSlot


class AvailabilityRuleInline(admin.TabularInline):
    model = AvailabilityRule
    extra = 0


class BlockedTimeInline(admin.TabularInline):
    model = BlockedTime
    extra = 0


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "timezone",
        "is_default",
        "is_active",
        "buffer_before",
        "buffer_after",
        "minimum_notice",
        "created_at",
    ]
    list_filter = ["is_default", "is_active"]
    search_fields = ["name", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [AvailabilityRuleInline, BlockedTimeInline]


@admin.register(AvailabilityRule)
class AvailabilityRuleAdmin(admin.ModelAdmin):
    list_display = [
        "calendar",
        "rule_type",
        "day_of_week",
        "specific_date",
        "start_time",
        "end_time",
        "is_available",
    ]
    list_filter = ["rule_type", "is_available", "day_of_week"]
    search_fields = ["calendar__name", "calendar__user__email"]


@admin.register(BlockedTime)
class BlockedTimeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "calendar",
        "start_datetime",
        "end_datetime",
        "is_all_day",
        "is_recurring",
    ]
    list_filter = ["is_all_day", "is_recurring"]
    search_fields = ["title", "calendar__name"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = [
        "calendar",
        "start_datetime",
        "end_datetime",
        "status",
    ]
    list_filter = ["status"]
    search_fields = ["calendar__name"]
