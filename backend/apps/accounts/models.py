"""
Account models: User, Organization, TeamMember.
Supports individual users and team/organization-based scheduling.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class UserManager(BaseUserManager):
    """Custom user manager using email as the primary identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email authentication.
    Includes profile fields relevant to scheduling.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    timezone = models.CharField(
        max_length=63,
        default="America/New_York",
        help_text="IANA timezone identifier",
    )
    date_format = models.CharField(
        max_length=20,
        default="MM/DD/YYYY",
        choices=[
            ("MM/DD/YYYY", "MM/DD/YYYY"),
            ("DD/MM/YYYY", "DD/MM/YYYY"),
            ("YYYY-MM-DD", "YYYY-MM-DD"),
        ],
    )
    time_format = models.CharField(
        max_length=5,
        default="12h",
        choices=[("12h", "12 hour"), ("24h", "24 hour")],
    )
    welcome_message = models.TextField(
        max_length=1000,
        blank=True,
        help_text="Default welcome message shown on booking pages",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.first_name}-{self.last_name}")
            slug = base_slug
            counter = 1
            while User.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def update_last_active(self):
        self.last_active_at = timezone.now()
        self.save(update_fields=["last_active_at"])


class Organization(models.Model):
    """
    Organization for team scheduling.
    Users can belong to multiple organizations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="org_logos/", blank=True, null=True)
    website = models.URLField(blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )

    # Billing / subscription tier
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Professional"),
        ("team", "Team"),
        ("enterprise", "Enterprise"),
    ]
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")

    # Settings
    default_timezone = models.CharField(max_length=63, default="America/New_York")
    booking_page_branding = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom branding: colors, fonts, logo position",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "organization"
        verbose_name_plural = "organizations"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.members.filter(is_active=True).count()


class TeamMember(models.Model):
    """
    Membership link between User and Organization.
    Supports role-based access control within teams.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)

    # Scheduling preferences within the org
    can_be_booked = models.BooleanField(
        default=True,
        help_text="Whether this member can receive bookings",
    )
    max_daily_bookings = models.PositiveIntegerField(
        default=0,
        help_text="Maximum bookings per day (0 = unlimited)",
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "organization"]
        ordering = ["joined_at"]
        verbose_name = "team member"
        verbose_name_plural = "team members"

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    @property
    def is_admin_or_owner(self):
        return self.role in ("owner", "admin")
