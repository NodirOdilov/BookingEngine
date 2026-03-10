"""
Views for accounts app: authentication, user profiles, organizations, team management.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Organization, TeamMember
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    TeamMemberInviteSerializer,
    TeamMemberSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token endpoint that includes user data."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Registration successful.",
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_object(self):
        user = self.request.user
        user.update_last_active()
        return user


class ChangePasswordView(generics.UpdateAPIView):
    """Change the authenticated user's password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class PublicUserProfileView(generics.RetrieveAPIView):
    """Public-facing user profile (for booking pages)."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    queryset = User.objects.filter(is_active=True)

    def get_serializer(self, *args, **kwargs):
        """Restrict fields for public view."""
        serializer = super().get_serializer(*args, **kwargs)
        public_fields = {
            "id", "first_name", "last_name", "full_name",
            "slug", "avatar", "bio", "timezone", "welcome_message",
        }
        for field_name in list(serializer.fields.keys()):
            if field_name not in public_fields:
                serializer.fields.pop(field_name)
        return serializer


class OrganizationViewSet(viewsets.ModelViewSet):
    """CRUD operations for organizations."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user,
            members__is_active=True,
        ).distinct()

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """List all members of the organization."""
        org = self.get_object()
        members = TeamMember.objects.filter(organization=org).select_related("user")
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Invite a user to the organization."""
        org = self.get_object()

        # Check permissions
        membership = TeamMember.objects.filter(
            user=request.user,
            organization=org,
        ).first()
        if not membership or not membership.is_admin_or_owner:
            return Response(
                {"detail": "Only admins and owners can invite members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TeamMemberInviteSerializer(
            data=request.data,
            context={"organization": org},
        )
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        # Find or note the user
        try:
            invited_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No user found with that email. They must register first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        team_member = TeamMember.objects.create(
            user=invited_user,
            organization=org,
            role=role,
            invited_by=request.user,
            invited_at=timezone.now(),
        )

        return Response(
            TeamMemberSerializer(team_member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """Remove a member from the organization."""
        org = self.get_object()

        membership = TeamMember.objects.filter(
            user=request.user,
            organization=org,
        ).first()
        if not membership or not membership.is_admin_or_owner:
            return Response(
                {"detail": "Only admins and owners can remove members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        member_id = request.data.get("member_id")
        if not member_id:
            return Response(
                {"detail": "member_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            member = TeamMember.objects.get(id=member_id, organization=org)
        except TeamMember.DoesNotExist:
            return Response(
                {"detail": "Member not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if member.role == "owner":
            return Response(
                {"detail": "Cannot remove the organization owner."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.is_active = False
        member.save()

        return Response(
            {"message": "Member removed successfully."},
            status=status.HTTP_200_OK,
        )
