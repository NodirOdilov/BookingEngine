"""
Serializers for accounts app: registration, login, user profile, organizations, team members.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Organization, TeamMember

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT token response with user data."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserProfileSerializer(self.user).data
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Handles user registration with password validation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "timezone",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile serializer."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "slug",
            "phone",
            "avatar",
            "bio",
            "timezone",
            "date_format",
            "time_format",
            "welcome_message",
            "is_email_verified",
            "created_at",
            "last_active_at",
        ]
        read_only_fields = ["id", "email", "slug", "is_email_verified", "created_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "bio",
            "timezone",
            "date_format",
            "time_format",
            "welcome_message",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Handles password change requests."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user representation for nested serializers."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "avatar", "slug"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Full organization serializer."""

    owner = UserMinimalSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "website",
            "owner",
            "plan",
            "default_timezone",
            "booking_page_branding",
            "member_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "owner", "created_at", "updated_at"]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an organization."""

    class Meta:
        model = Organization
        fields = ["name", "website", "default_timezone", "logo"]

    def create(self, validated_data):
        user = self.context["request"].user
        org = Organization.objects.create(owner=user, **validated_data)
        # Automatically add the creator as owner member
        TeamMember.objects.create(
            user=user,
            organization=org,
            role="owner",
        )
        return org


class TeamMemberSerializer(serializers.ModelSerializer):
    """Full team member serializer."""

    user = UserMinimalSerializer(read_only=True)
    invited_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "user",
            "organization",
            "role",
            "is_active",
            "can_be_booked",
            "max_daily_bookings",
            "invited_by",
            "invited_at",
            "joined_at",
        ]
        read_only_fields = ["id", "organization", "invited_by", "invited_at", "joined_at"]


class TeamMemberInviteSerializer(serializers.Serializer):
    """Serializer for inviting a user to an organization."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=TeamMember.ROLE_CHOICES,
        default="member",
    )

    def validate_email(self, value):
        org = self.context.get("organization")
        if org and TeamMember.objects.filter(
            organization=org,
            user__email=value,
        ).exists():
            raise serializers.ValidationError(
                "This user is already a member of the organization."
            )
        return value
