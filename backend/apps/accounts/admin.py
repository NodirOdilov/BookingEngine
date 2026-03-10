"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, TeamMember, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "slug",
        "timezone",
        "is_active",
        "is_staff",
        "created_at",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "is_email_verified"]
    search_fields = ["email", "first_name", "last_name", "slug"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "slug",
                    "phone",
                    "avatar",
                    "bio",
                    "welcome_message",
                )
            },
        ),
        (
            "Preferences",
            {"fields": ("timezone", "date_format", "time_format")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("last_login", "last_active_at", "created_at")},
        ),
    )
    readonly_fields = ["created_at", "last_active_at"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    readonly_fields = ["joined_at"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "plan", "member_count", "is_active", "created_at"]
    list_filter = ["plan", "is_active"]
    search_fields = ["name", "slug"]
    inlines = [TeamMemberInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "organization",
        "role",
        "is_active",
        "can_be_booked",
        "joined_at",
    ]
    list_filter = ["role", "is_active", "can_be_booked"]
    search_fields = ["user__email", "organization__name"]
    readonly_fields = ["joined_at"]
