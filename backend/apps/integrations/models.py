"""
Integration models: CalendarIntegration, WebhookEndpoint.
Manages connections to Google Calendar, Outlook, Zoom, and custom webhooks.
"""

import uuid

from django.conf import settings
from django.db import models


class CalendarIntegration(models.Model):
    """
    External calendar integration (Google Calendar, Outlook, etc.).
    Stores OAuth tokens and sync settings.
    """

    PROVIDER_CHOICES = [
        ("google", "Google Calendar"),
        ("outlook", "Microsoft Outlook"),
        ("apple", "Apple Calendar"),
    ]

    SYNC_STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("error", "Error"),
        ("disconnected", "Disconnected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_integrations",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_email = models.EmailField(
        blank=True,
        help_text="Email associated with the provider account",
    )

    # OAuth tokens (encrypted in production)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Sync settings
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default="active",
    )
    sync_direction = models.CharField(
        max_length=20,
        choices=[
            ("both", "Both Directions"),
            ("import_only", "Import Only"),
            ("export_only", "Export Only"),
        ],
        default="both",
    )
    external_calendar_id = models.CharField(
        max_length=500,
        blank=True,
        help_text="ID of the specific calendar to sync with",
    )
    external_calendar_name = models.CharField(max_length=255, blank=True)

    # Conflict checking
    check_conflicts = models.BooleanField(
        default=True,
        help_text="Block bookings that conflict with external calendar events",
    )

    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_error = models.TextField(blank=True)
    sync_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Incremental sync token from provider",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "provider", "provider_email"]
        verbose_name = "calendar integration"
        verbose_name_plural = "calendar integrations"

    def __str__(self):
        return f"{self.get_provider_display()} - {self.provider_email} ({self.user.email})"

    @property
    def is_token_expired(self):
        from django.utils import timezone
        if self.token_expires_at is None:
            return True
        return timezone.now() >= self.token_expires_at


class WebhookEndpoint(models.Model):
    """
    Custom webhook endpoints for event notifications.
    Users can register webhooks to receive booking events.
    """

    EVENT_CHOICES = [
        ("booking.created", "Booking Created"),
        ("booking.confirmed", "Booking Confirmed"),
        ("booking.cancelled", "Booking Cancelled"),
        ("booking.rescheduled", "Booking Rescheduled"),
        ("booking.completed", "Booking Completed"),
        ("payment.completed", "Payment Completed"),
        ("payment.refunded", "Payment Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webhook_endpoints",
    )
    url = models.URLField(max_length=500)
    secret = models.CharField(
        max_length=255,
        help_text="Secret for signing webhook payloads",
    )
    events = models.JSONField(
        default=list,
        help_text="List of events to subscribe to",
    )
    description = models.CharField(max_length=255, blank=True)

    # Health tracking
    is_active = models.BooleanField(default=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    total_failures = models.PositiveIntegerField(default=0)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_response_code = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "webhook endpoint"
        verbose_name_plural = "webhook endpoints"

    def __str__(self):
        return f"Webhook: {self.url} ({self.user.email})"

    @property
    def failure_rate(self):
        if self.total_deliveries == 0:
            return 0
        return round(self.total_failures / self.total_deliveries * 100, 1)
