"""
Calendar models: Calendar, AvailabilityRule, BlockedTime, TimeSlot.
Handles availability windows, weekly schedules, date overrides, and blocked periods.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Calendar(models.Model):
    """
    A user's calendar that holds availability rules.
    Users can have multiple calendars (e.g., work, personal).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendars",
    )
    name = models.CharField(max_length=255, default="My Calendar")
    description = models.TextField(blank=True)
    timezone = models.CharField(
        max_length=63,
        default="America/New_York",
        help_text="IANA timezone for this calendar",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the user's primary calendar",
    )
    is_active = models.BooleanField(default=True)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex color for calendar display",
    )

    # Buffer settings
    buffer_before = models.PositiveIntegerField(
        default=0,
        help_text="Buffer time before events (minutes)",
    )
    buffer_after = models.PositiveIntegerField(
        default=0,
        help_text="Buffer time after events (minutes)",
    )

    # Scheduling limits
    minimum_notice = models.PositiveIntegerField(
        default=4,
        help_text="Minimum hours notice before booking",
    )
    max_days_ahead = models.PositiveIntegerField(
        default=60,
        help_text="How many days into the future bookings are allowed",
    )
    max_bookings_per_day = models.PositiveIntegerField(
        default=0,
        help_text="Maximum bookings per day (0 = unlimited)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name = "calendar"
        verbose_name_plural = "calendars"

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        # Ensure only one default calendar per user
        if self.is_default:
            Calendar.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class AvailabilityRule(models.Model):
    """
    Defines when a user is available for bookings.
    Supports both recurring weekly rules and date-specific overrides.
    """

    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    RULE_TYPE_CHOICES = [
        ("weekly", "Weekly Recurring"),
        ("date_override", "Date Override"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="availability_rules",
    )

    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        default="weekly",
    )

    # For weekly rules
    day_of_week = models.IntegerField(
        choices=DAY_CHOICES,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
    )

    # For date overrides
    specific_date = models.DateField(
        null=True,
        blank=True,
        help_text="For date-specific overrides",
    )

    start_time = models.TimeField(help_text="Availability start time")
    end_time = models.TimeField(help_text="Availability end time")

    is_available = models.BooleanField(
        default=True,
        help_text="False = mark this time as unavailable (date override)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name = "availability rule"
        verbose_name_plural = "availability rules"

    def __str__(self):
        if self.rule_type == "weekly":
            day_name = dict(self.DAY_CHOICES).get(self.day_of_week, "Unknown")
            return f"{day_name} {self.start_time}-{self.end_time}"
        return f"{self.specific_date} {self.start_time}-{self.end_time}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        if self.rule_type == "weekly" and self.day_of_week is None:
            raise ValidationError("Weekly rules require a day of the week.")

        if self.rule_type == "date_override" and self.specific_date is None:
            raise ValidationError("Date overrides require a specific date.")


class BlockedTime(models.Model):
    """
    Explicit blocked-out time periods (vacations, meetings, etc.).
    Takes priority over availability rules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="blocked_times",
    )
    title = models.CharField(max_length=255, default="Blocked")
    reason = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(
        max_length=255,
        blank=True,
        help_text="RRULE string for recurring blocks",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_datetime"]
        verbose_name = "blocked time"
        verbose_name_plural = "blocked times"

    def __str__(self):
        return f"{self.title}: {self.start_datetime} - {self.end_datetime}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError("Start must be before end.")


class TimeSlot(models.Model):
    """
    Pre-computed available time slots for efficient querying.
    Regenerated when availability rules or bookings change.
    """

    STATUS_CHOICES = [
        ("available", "Available"),
        ("booked", "Booked"),
        ("blocked", "Blocked"),
        ("tentative", "Tentative"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="time_slots",
    )
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        db_index=True,
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_slots",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_datetime"]
        indexes = [
            models.Index(fields=["calendar", "start_datetime", "status"]),
            models.Index(fields=["calendar", "start_datetime", "end_datetime"]),
        ]
        verbose_name = "time slot"
        verbose_name_plural = "time slots"

    def __str__(self):
        return f"{self.calendar.name}: {self.start_datetime} - {self.end_datetime} ({self.status})"
