"""
Booking page models: BookingPage, EmbedWidget.
Manages public-facing booking pages with custom branding.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


class BookingPage(models.Model):
    """
    A customizable public booking page for a user or organization.
    Supports custom branding, colors, and messaging.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="booking_pages",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="booking_pages",
    )

    # Page content
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    welcome_message = models.TextField(blank=True)
    logo = models.ImageField(upload_to="booking_pages/logos/", blank=True, null=True)
    cover_image = models.ImageField(
        upload_to="booking_pages/covers/", blank=True, null=True
    )

    # Branding
    primary_color = models.CharField(max_length=7, default="#3B82F6")
    text_color = models.CharField(max_length=7, default="#1F2937")
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    font_family = models.CharField(
        max_length=100,
        default="Inter",
        choices=[
            ("Inter", "Inter"),
            ("Roboto", "Roboto"),
            ("Open Sans", "Open Sans"),
            ("Lato", "Lato"),
            ("Poppins", "Poppins"),
        ],
    )

    # SEO and meta
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)

    # Settings
    show_powered_by = models.BooleanField(default=True)
    show_avatar = models.BooleanField(default=True)
    show_event_duration = models.BooleanField(default=True)
    show_event_description = models.BooleanField(default=True)
    show_timezone_selector = models.BooleanField(default=True)

    # Custom domain
    custom_domain = models.CharField(max_length=255, blank=True, unique=True, null=True)
    is_custom_domain_verified = models.BooleanField(default=False)

    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "booking page"
        verbose_name_plural = "booking pages"

    def __str__(self):
        return f"Booking Page: {self.user.email}"

    @property
    def public_url(self):
        return f"/p/{self.user.slug}"


class EmbedWidget(models.Model):
    """
    Embeddable booking widget for external websites.
    Generates embed code (inline or popup) for integration.
    """

    EMBED_TYPE_CHOICES = [
        ("inline", "Inline"),
        ("popup", "Popup Button"),
        ("floating", "Floating Button"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="embed_widgets",
    )
    event_type = models.ForeignKey(
        "event_types.EventType",
        on_delete=models.CASCADE,
        related_name="embed_widgets",
    )

    name = models.CharField(max_length=255, default="Booking Widget")
    embed_type = models.CharField(
        max_length=20,
        choices=EMBED_TYPE_CHOICES,
        default="inline",
    )
    embed_token = models.CharField(
        max_length=64,
        unique=True,
        default=lambda: get_random_string(32),
    )

    # Popup button settings
    button_text = models.CharField(max_length=100, default="Book a Meeting")
    button_color = models.CharField(max_length=7, default="#3B82F6")
    button_text_color = models.CharField(max_length=7, default="#FFFFFF")
    button_position = models.CharField(
        max_length=20,
        choices=[
            ("bottom-right", "Bottom Right"),
            ("bottom-left", "Bottom Left"),
            ("center", "Center"),
        ],
        default="bottom-right",
    )

    # Dimensions for inline embed
    width = models.CharField(max_length=20, default="100%")
    height = models.CharField(max_length=20, default="700px")

    # Tracking
    total_views = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "embed widget"
        verbose_name_plural = "embed widgets"

    def __str__(self):
        return f"{self.name} ({self.embed_type})"

    @property
    def embed_code(self):
        base_url = settings.FRONTEND_URL
        if self.embed_type == "inline":
            return (
                f'<iframe src="{base_url}/embed/{self.embed_token}" '
                f'width="{self.width}" height="{self.height}" '
                f'frameborder="0" scrolling="no"></iframe>'
            )
        return (
            f'<script src="{base_url}/embed.js" '
            f'data-token="{self.embed_token}" '
            f'data-type="{self.embed_type}" '
            f'data-text="{self.button_text}" '
            f'data-color="{self.button_color}"></script>'
        )
