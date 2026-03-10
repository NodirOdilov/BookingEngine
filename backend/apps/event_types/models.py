"""
Event type models: EventType, EventTypeSettings, Location.
Defines the types of appointments that can be booked.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class EventType(models.Model):
    """
    A bookable event type (e.g., "30 Min Meeting", "1 Hour Consultation").
    Linked to a calendar and optionally to an organization.
    """

    SCHEDULING_TYPE_CHOICES = [
        ("one_on_one", "One on One"),
        ("round_robin", "Round Robin"),
        ("collective", "Collective"),
        ("group", "Group"),
    ]

    COLOR_CHOICES = [
        ("#3B82F6", "Blue"),
        ("#10B981", "Green"),
        ("#F59E0B", "Amber"),
        ("#EF4444", "Red"),
        ("#8B5CF6", "Purple"),
        ("#EC4899", "Pink"),
        ("#06B6D4", "Cyan"),
        ("#F97316", "Orange"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_types",
    )
    calendar = models.ForeignKey(
        "calendars.Calendar",
        on_delete=models.CASCADE,
        related_name="event_types",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_types",
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(
        blank=True,
        help_text="Instructions shown to invitee after booking",
    )
    color = models.CharField(max_length=7, default="#3B82F6", choices=COLOR_CHOICES)

    # Duration
    duration = models.PositiveIntegerField(
        default=30,
        help_text="Duration in minutes",
    )
    DURATION_CHOICES = [
        (15, "15 minutes"),
        (30, "30 minutes"),
        (45, "45 minutes"),
        (60, "1 hour"),
        (90, "1.5 hours"),
        (120, "2 hours"),
    ]

    # Scheduling type
    scheduling_type = models.CharField(
        max_length=20,
        choices=SCHEDULING_TYPE_CHOICES,
        default="one_on_one",
    )

    # For group events
    max_participants = models.PositiveIntegerField(
        default=1,
        help_text="Maximum participants per slot (1 for one-on-one)",
    )

    # Pricing
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price in the default currency",
    )
    currency = models.CharField(max_length=3, default="USD")

    # Buffer overrides (overrides calendar defaults)
    buffer_before = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override calendar buffer (minutes)",
    )
    buffer_after = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override calendar buffer (minutes)",
    )

    # Scheduling limits
    minimum_notice = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override calendar minimum notice (hours)",
    )
    max_bookings_per_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override calendar max bookings per day",
    )

    # Custom questions
    custom_questions = models.JSONField(
        default=list,
        blank=True,
        help_text='List of custom questions: [{"label": "...", "type": "text", "required": true}]',
    )

    # Confirmation settings
    requires_confirmation = models.BooleanField(
        default=False,
        help_text="Host must confirm bookings manually",
    )
    confirmation_redirect_url = models.URLField(
        blank=True,
        help_text="Redirect URL after booking confirmation",
    )

    is_active = models.BooleanField(default=True)
    is_secret = models.BooleanField(
        default=False,
        help_text="Hidden from public booking page, only accessible via direct link",
    )

    # Team scheduling
    team_members = models.ManyToManyField(
        "accounts.TeamMember",
        blank=True,
        related_name="assigned_event_types",
        help_text="Team members assigned to this event type",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ["user", "slug"]
        verbose_name = "event type"
        verbose_name_plural = "event types"

    def __str__(self):
        return f"{self.name} ({self.duration} min)"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while (
                EventType.objects.filter(user=self.user, slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def effective_buffer_before(self):
        if self.buffer_before is not None:
            return self.buffer_before
        return self.calendar.buffer_before

    @property
    def effective_buffer_after(self):
        if self.buffer_after is not None:
            return self.buffer_after
        return self.calendar.buffer_after

    @property
    def effective_minimum_notice(self):
        if self.minimum_notice is not None:
            return self.minimum_notice
        return self.calendar.minimum_notice


class Location(models.Model):
    """
    Location options for an event type.
    Supports multiple location types per event.
    """

    LOCATION_TYPE_CHOICES = [
        ("in_person", "In Person"),
        ("phone_incoming", "Phone (invitee calls)"),
        ("phone_outgoing", "Phone (I will call)"),
        ("google_meet", "Google Meet"),
        ("zoom", "Zoom"),
        ("microsoft_teams", "Microsoft Teams"),
        ("custom_link", "Custom Link"),
        ("ask_invitee", "Ask Invitee"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    location_type = models.CharField(max_length=30, choices=LOCATION_TYPE_CHOICES)
    address = models.TextField(
        blank=True,
        help_text="Physical address or meeting link",
    )
    phone_number = models.CharField(max_length=20, blank=True)
    additional_info = models.TextField(blank=True)
    position = models.PositiveIntegerField(
        default=0,
        help_text="Display order",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
        verbose_name = "location"
        verbose_name_plural = "locations"

    def __str__(self):
        return f"{self.get_location_type_display()} - {self.event_type.name}"


class EventTypeSettings(models.Model):
    """
    Extended settings for an event type.
    Covers reminder configuration, booking limits, and display options.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.OneToOneField(
        EventType,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    # Reminder settings
    email_reminder_enabled = models.BooleanField(default=True)
    email_reminder_minutes = models.JSONField(
        default=list,
        help_text="List of minutes before event to send email reminders, e.g. [1440, 60]",
    )
    sms_reminder_enabled = models.BooleanField(default=False)
    sms_reminder_minutes = models.JSONField(
        default=list,
        help_text="List of minutes before event to send SMS reminders",
    )

    # Follow-up
    follow_up_enabled = models.BooleanField(default=False)
    follow_up_delay_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours after event to send follow-up email",
    )

    # Booking limits
    max_events_per_day = models.PositiveIntegerField(
        default=0,
        help_text="0 = unlimited",
    )
    rolling_days_window = models.PositiveIntegerField(
        default=60,
        help_text="Days into the future to allow bookings",
    )
    slot_interval = models.PositiveIntegerField(
        default=30,
        help_text="Minutes between slot start times",
    )

    # Display options
    show_remaining_slots = models.BooleanField(
        default=False,
        help_text="Show how many slots are left on a given day",
    )
    allow_cancellation = models.BooleanField(default=True)
    allow_rescheduling = models.BooleanField(default=True)
    cancellation_notice_hours = models.PositiveIntegerField(
        default=24,
        help_text="Minimum hours before event to allow cancellation",
    )

    class Meta:
        verbose_name = "event type settings"
        verbose_name_plural = "event type settings"

    def __str__(self):
        return f"Settings for {self.event_type.name}"

    def save(self, *args, **kwargs):
        if not self.email_reminder_minutes:
            self.email_reminder_minutes = [1440, 60]  # 24h and 1h before
        super().save(*args, **kwargs)
