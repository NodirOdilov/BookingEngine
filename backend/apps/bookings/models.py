"""
Booking models: Booking, BookingNote, BookingReminder, RescheduleHistory.
Core transactional models for the scheduling engine.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def generate_booking_reference():
    """Generate a unique human-readable booking reference code."""
    return f"BK-{get_random_string(8, 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789')}"


class Booking(models.Model):
    """
    A scheduled appointment between a host (provider) and an invitee (client).
    Central model linking event types, calendars, and participants.
    """

    STATUS_CHOICES = [
        ("pending", "Pending Confirmation"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
        ("rescheduled", "Rescheduled"),
    ]

    CANCELLATION_REASON_CHOICES = [
        ("host_cancelled", "Host Cancelled"),
        ("invitee_cancelled", "Invitee Cancelled"),
        ("conflict", "Schedule Conflict"),
        ("payment_failed", "Payment Failed"),
        ("system", "System Cancellation"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(
        max_length=20,
        unique=True,
        default=generate_booking_reference,
        db_index=True,
    )

    # Relationships
    event_type = models.ForeignKey(
        "event_types.EventType",
        on_delete=models.SET_NULL,
        null=True,
        related_name="bookings",
    )
    calendar = models.ForeignKey(
        "calendars.Calendar",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_bookings",
    )

    # Invitee details (may or may not be a registered user)
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitee_bookings",
    )
    invitee_name = models.CharField(max_length=255)
    invitee_email = models.EmailField(db_index=True)
    invitee_phone = models.CharField(max_length=20, blank=True)
    invitee_timezone = models.CharField(max_length=63, default="UTC")
    invitee_notes = models.TextField(
        blank=True,
        help_text="Notes provided by invitee during booking",
    )

    # Custom question responses
    custom_responses = models.JSONField(
        default=dict,
        blank=True,
        help_text="Responses to event type custom questions",
    )

    # Scheduling
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(
        max_length=30,
        choices=CANCELLATION_REASON_CHOICES,
        blank=True,
    )
    cancellation_notes = models.TextField(blank=True)

    # Location
    location_type = models.CharField(max_length=30, blank=True)
    location_detail = models.TextField(
        blank=True,
        help_text="Address, meeting link, or phone number",
    )
    meeting_link = models.URLField(blank=True)

    # Payment
    is_paid = models.BooleanField(default=False)
    payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    payment_currency = models.CharField(max_length=3, default="USD")
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("not_required", "Not Required"),
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("refunded", "Refunded"),
            ("failed", "Failed"),
        ],
        default="not_required",
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    # Tracking
    source = models.CharField(
        max_length=30,
        choices=[
            ("booking_page", "Booking Page"),
            ("embed", "Embedded Widget"),
            ("api", "API"),
            ("admin", "Admin"),
            ("import", "Import"),
        ],
        default="booking_page",
    )
    utm_source = models.CharField(max_length=255, blank=True)
    utm_medium = models.CharField(max_length=255, blank=True)
    utm_campaign = models.CharField(max_length=255, blank=True)

    # External calendar sync
    google_event_id = models.CharField(max_length=255, blank=True)
    outlook_event_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["host", "start_time", "status"]),
            models.Index(fields=["calendar", "start_time", "status"]),
            models.Index(fields=["invitee_email", "status"]),
            models.Index(fields=["start_time", "end_time"]),
        ]
        verbose_name = "booking"
        verbose_name_plural = "bookings"

    def __str__(self):
        return f"{self.reference}: {self.invitee_name} with {self.host.email}"

    @property
    def is_upcoming(self):
        return self.start_time > timezone.now() and self.status == "confirmed"

    @property
    def is_past(self):
        return self.end_time < timezone.now()

    @property
    def can_cancel(self):
        if self.status not in ("pending", "confirmed"):
            return False
        if self.event_type and hasattr(self.event_type, "settings"):
            notice_hours = self.event_type.settings.cancellation_notice_hours
            cutoff = self.start_time - timedelta(hours=notice_hours)
            return timezone.now() < cutoff
        return self.start_time > timezone.now()

    @property
    def can_reschedule(self):
        if self.status not in ("pending", "confirmed"):
            return False
        if self.event_type and hasattr(self.event_type, "settings"):
            if not self.event_type.settings.allow_rescheduling:
                return False
        return self.start_time > timezone.now()

    def confirm(self):
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at", "updated_at"])

    def cancel(self, reason="other", notes=""):
        self.status = "cancelled"
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        self.save(update_fields=[
            "status", "cancelled_at", "cancellation_reason",
            "cancellation_notes", "updated_at",
        ])

    def mark_completed(self):
        self.status = "completed"
        self.save(update_fields=["status", "updated_at"])

    def mark_no_show(self):
        self.status = "no_show"
        self.save(update_fields=["status", "updated_at"])


class BookingNote(models.Model):
    """Internal notes attached to a booking by the host or team members."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="booking_notes",
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=True,
        help_text="Internal notes are only visible to the host",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "booking note"
        verbose_name_plural = "booking notes"

    def __str__(self):
        return f"Note on {self.booking.reference} by {self.author.email}"


class RescheduleHistory(models.Model):
    """Tracks reschedule history for a booking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="reschedule_history",
    )
    previous_start = models.DateTimeField()
    previous_end = models.DateTimeField()
    new_start = models.DateTimeField()
    new_end = models.DateTimeField()
    rescheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    rescheduled_by_email = models.EmailField(blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "reschedule history"
        verbose_name_plural = "reschedule histories"

    def __str__(self):
        return f"Reschedule {self.booking.reference}: {self.previous_start} -> {self.new_start}"


class BookingReminder(models.Model):
    """Scheduled reminders for bookings."""

    REMINDER_TYPE_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
    ]

    RECIPIENT_CHOICES = [
        ("host", "Host"),
        ("invitee", "Invitee"),
        ("both", "Both"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPE_CHOICES)
    recipient = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
    minutes_before = models.PositiveIntegerField(
        help_text="Minutes before booking start to send reminder",
    )
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["is_sent", "scheduled_at"]),
        ]
        verbose_name = "booking reminder"
        verbose_name_plural = "booking reminders"

    def __str__(self):
        return f"{self.reminder_type} reminder for {self.booking.reference}"
