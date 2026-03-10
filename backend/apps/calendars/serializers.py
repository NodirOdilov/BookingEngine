"""
Serializers for calendars app.
"""

from rest_framework import serializers

from .models import AvailabilityRule, BlockedTime, Calendar, TimeSlot


class CalendarSerializer(serializers.ModelSerializer):
    """Full calendar serializer."""

    availability_rules_count = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Calendar
        fields = [
            "id",
            "user",
            "user_email",
            "name",
            "description",
            "timezone",
            "is_default",
            "is_active",
            "color",
            "buffer_before",
            "buffer_after",
            "minimum_notice",
            "max_days_ahead",
            "max_bookings_per_day",
            "availability_rules_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_availability_rules_count(self, obj):
        return obj.availability_rules.count()


class CalendarCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating calendars."""

    class Meta:
        model = Calendar
        fields = [
            "name",
            "description",
            "timezone",
            "is_default",
            "color",
            "buffer_before",
            "buffer_after",
            "minimum_notice",
            "max_days_ahead",
            "max_bookings_per_day",
        ]


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    """Serializer for availability rules."""

    day_name = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilityRule
        fields = [
            "id",
            "calendar",
            "rule_type",
            "day_of_week",
            "day_name",
            "specific_date",
            "start_time",
            "end_time",
            "is_available",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_day_name(self, obj):
        if obj.day_of_week is not None:
            return dict(AvailabilityRule.DAY_CHOICES).get(obj.day_of_week)
        return None

    def validate(self, data):
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        rule_type = data.get("rule_type", "weekly")
        if rule_type == "weekly" and data.get("day_of_week") is None:
            raise serializers.ValidationError(
                "Weekly rules require a day_of_week."
            )
        if rule_type == "date_override" and data.get("specific_date") is None:
            raise serializers.ValidationError(
                "Date overrides require a specific_date."
            )
        return data


class AvailabilityRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating availability rules."""

    class Meta:
        model = AvailabilityRule
        fields = [
            "rule_type",
            "day_of_week",
            "specific_date",
            "start_time",
            "end_time",
            "is_available",
        ]

    def validate(self, data):
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")
        return data


class BulkAvailabilitySerializer(serializers.Serializer):
    """Serializer for setting full weekly availability at once."""

    rules = AvailabilityRuleCreateSerializer(many=True)

    def validate_rules(self, value):
        if not value:
            raise serializers.ValidationError("At least one rule is required.")
        return value


class BlockedTimeSerializer(serializers.ModelSerializer):
    """Serializer for blocked time periods."""

    class Meta:
        model = BlockedTime
        fields = [
            "id",
            "calendar",
            "title",
            "reason",
            "start_datetime",
            "end_datetime",
            "is_all_day",
            "is_recurring",
            "recurrence_rule",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        start = data.get("start_datetime")
        end = data.get("end_datetime")
        if start and end and start >= end:
            raise serializers.ValidationError(
                "Start datetime must be before end datetime."
            )
        return data


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for computed time slots."""

    class Meta:
        model = TimeSlot
        fields = [
            "id",
            "calendar",
            "start_datetime",
            "end_datetime",
            "status",
            "booking",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AvailableSlotsQuerySerializer(serializers.Serializer):
    """Query parameters for fetching available slots."""

    date = serializers.DateField(required=True)
    timezone = serializers.CharField(max_length=63, default="UTC")
    duration = serializers.IntegerField(min_value=5, max_value=480, default=30)
    event_type_id = serializers.UUIDField(required=False)
