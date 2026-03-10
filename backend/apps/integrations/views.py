"""
Views for integrations app: calendar connections, OAuth callbacks, webhooks.
"""

import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.response import Response

from .models import CalendarIntegration, WebhookEndpoint
from .serializers import (
    CalendarIntegrationSerializer,
    CalendarIntegrationUpdateSerializer,
    WebhookEndpointCreateSerializer,
    WebhookEndpointSerializer,
)
from .services import GoogleCalendarService

logger = logging.getLogger(__name__)


class CalendarIntegrationViewSet(viewsets.ModelViewSet):
    """Manage calendar integrations."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return CalendarIntegrationUpdateSerializer
        return CalendarIntegrationSerializer

    def get_queryset(self):
        return CalendarIntegration.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="google/connect")
    def google_connect(self, request):
        """Initiate Google Calendar OAuth flow."""
        service = GoogleCalendarService()
        state = str(uuid.uuid4())

        # Store state in session for verification
        request.session["google_oauth_state"] = state
        request.session["google_oauth_user_id"] = str(request.user.id)

        auth_url = service.get_authorization_url(state)
        return Response({"authorization_url": auth_url})

    @action(detail=True, methods=["get"], url_path="calendars")
    def list_calendars(self, request, pk=None):
        """List available calendars for a connected integration."""
        integration = self.get_object()

        if integration.provider == "google":
            service = GoogleCalendarService()
            try:
                calendars = service.list_calendars(integration)
                return Response({"calendars": calendars})
            except Exception as exc:
                logger.error("Failed to list Google calendars: %s", str(exc))
                return Response(
                    {"detail": "Failed to fetch calendars."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {"detail": "Calendar listing not supported for this provider."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Manually trigger a sync for a calendar integration."""
        integration = self.get_object()
        from .services import CalendarSyncService

        try:
            service = CalendarSyncService()
            service.sync_integration(integration)
            return Response({
                "message": "Sync completed successfully.",
                "last_synced_at": integration.last_synced_at.isoformat(),
            })
        except Exception as exc:
            return Response(
                {"detail": f"Sync failed: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        """Disconnect a calendar integration."""
        integration = self.get_object()
        integration.sync_status = "disconnected"
        integration.is_active = False
        integration.access_token = ""
        integration.refresh_token = ""
        integration.save()
        return Response({"message": "Calendar disconnected."})


@api_view(["GET"])
@perm_classes([permissions.AllowAny])
def google_oauth_callback(request):
    """
    Handle Google OAuth callback.
    Exchanges code for tokens and creates the calendar integration.
    """
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    if error:
        return redirect(
            f"{settings.FRONTEND_URL}/settings/integrations?error={error}"
        )

    # Verify state
    stored_state = request.session.get("google_oauth_state")
    user_id = request.session.get("google_oauth_user_id")

    if not code or state != stored_state or not user_id:
        return redirect(
            f"{settings.FRONTEND_URL}/settings/integrations?error=invalid_state"
        )

    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect(
            f"{settings.FRONTEND_URL}/settings/integrations?error=user_not_found"
        )

    service = GoogleCalendarService()
    try:
        tokens = service.exchange_code(code)
    except Exception as exc:
        logger.error("Google token exchange failed: %s", str(exc))
        return redirect(
            f"{settings.FRONTEND_URL}/settings/integrations?error=token_exchange_failed"
        )

    # Create integration
    integration, created = CalendarIntegration.objects.update_or_create(
        user=user,
        provider="google",
        defaults={
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", ""),
            "token_expires_at": timezone.now() + timedelta(
                seconds=tokens.get("expires_in", 3600)
            ),
            "sync_status": "active",
            "is_active": True,
        },
    )

    # Fetch user's email from Google
    try:
        calendars = service.list_calendars(integration)
        primary = next((c for c in calendars if c["primary"]), None)
        if primary:
            integration.provider_email = primary["id"]
            integration.external_calendar_id = primary["id"]
            integration.external_calendar_name = primary["name"]
            integration.save()
    except Exception:
        pass

    return redirect(
        f"{settings.FRONTEND_URL}/settings/integrations?success=google"
    )


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """Manage webhook endpoints."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return WebhookEndpointCreateSerializer
        return WebhookEndpointSerializer

    def get_queryset(self):
        return WebhookEndpoint.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Send a test webhook delivery."""
        endpoint = self.get_object()
        from .services import WebhookDeliveryService

        service = WebhookDeliveryService()
        service._send_webhook(
            endpoint,
            event_type="test.ping",
            payload={"message": "Test webhook delivery from BookingEngine"},
        )

        return Response({
            "message": "Test webhook sent.",
            "last_response_code": endpoint.last_response_code,
        })
