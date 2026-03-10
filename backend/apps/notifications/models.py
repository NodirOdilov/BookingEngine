"""
Notification models: NotificationTemplate, NotificationLog, UserNotificationPreference.
Manages email templates, notification history, and user preferences.
"""

import uuid

from django.conf import settings
from django.db import models


class NotificationTemplate(models.Model):
    """
    Email notification templates.
    Supports variable substitution for dynamic content.
    """

    TEMPLATE_TYPE_CHOICES = [
        ("booking_created", "Booking Created"),
        ("booking_confirmed", "Booking Confirmed"),
        ("booking_cancelled", "Booking Cancelled"),
        ("booking_rescheduled", "Booking Rescheduled"),
        ("booking_reminder", "Booking Reminder"),
        ("booking_follow_up", "Booking Follow-Up"),
        ("daily_digest", "Daily Digest"),
        ("welcome", "Welcome Email"),
        ("password_reset", "Password Reset"),
        ("team_invitation", "Team Invitation"),
        ("payment_receipt", "Payment Receipt"),
        ("payment_refund", "Payment Refund"),
    ]

    RECIPIENT_CHOICES = [
        ("host", "Host"),
        ("invitee", "Invitee"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
    name = models.CharField(max_length=255)

    # Template content
    subject = models.CharField(max_length=500)
    body_html = models.TextField(help_text="HTML email body with template variables")
    body_text = models.TextField(
        blank=True,
        help_text="Plain text fallback",
    )

    # Customization
    is_default = models.BooleanField(
        default=False,
        help_text="System default template",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_templates",
        help_text="Organization-specific template override",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["template_type", "recipient_type"]
        verbose_name = "notification template"
        verbose_name_plural = "notification templates"

    def __str__(self):
        return f"{self.name} ({self.template_type} -> {self.recipient_type})"

    def render(self, context: dict) -> tuple:
        """
        Render the template with the given context.

        Returns:
            tuple of (subject, html_body, text_body)
        """
        subject = self.subject
        html_body = self.body_html
        text_body = self.body_text

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            html_body = html_body.replace(placeholder, str(value))
            text_body = text_body.replace(placeholder, str(value))

        return subject, html_body, text_body


class NotificationLog(models.Model):
    """
    Log of all sent notifications.
    Tracks delivery status for audit and debugging.
    """

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
        ("in_app", "In-App"),
    ]

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )

    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    notification_type = models.CharField(max_length=30)
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=255, blank=True)

    subject = models.CharField(max_length=500, blank=True)
    body_preview = models.TextField(
        blank=True,
        help_text="First 500 chars of the notification body",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="queued",
    )
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # External tracking
    external_message_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "channel"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]
        verbose_name = "notification log"
        verbose_name_plural = "notification logs"

    def __str__(self):
        return f"{self.notification_type} to {self.recipient_email} ({self.status})"


class UserNotificationPreference(models.Model):
    """
    Per-user notification preferences.
    Controls which notifications a user receives and via which channels.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    # Email notifications
    email_new_booking = models.BooleanField(default=True)
    email_booking_cancelled = models.BooleanField(default=True)
    email_booking_rescheduled = models.BooleanField(default=True)
    email_booking_reminder = models.BooleanField(default=True)
    email_daily_digest = models.BooleanField(default=True)
    email_payment_received = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)

    # SMS notifications
    sms_new_booking = models.BooleanField(default=False)
    sms_booking_cancelled = models.BooleanField(default=False)
    sms_booking_reminder = models.BooleanField(default=False)

    # Push notifications
    push_new_booking = models.BooleanField(default=True)
    push_booking_cancelled = models.BooleanField(default=True)
    push_booking_reminder = models.BooleanField(default=True)

    # Digest settings
    digest_time = models.TimeField(
        default="07:00",
        help_text="Time to receive daily digest (in user's timezone)",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "notification preference"
        verbose_name_plural = "notification preferences"

    def __str__(self):
        return f"Notification preferences: {self.user.email}"
