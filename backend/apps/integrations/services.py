"""
External calendar sync service for BookingEngine.
Handles Google Calendar and Outlook integration, OAuth flow, and event sync.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .models import CalendarIntegration, WebhookEndpoint

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar integration."""

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    CALENDAR_API = "https://www.googleapis.com/calendar/v3"

    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"

    def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access and refresh tokens."""
        response = requests.post(self.TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        })
        response.raise_for_status()
        data = response.json()

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_in": data.get("expires_in", 3600),
        }

    def refresh_access_token(self, integration: CalendarIntegration) -> str:
        """Refresh an expired access token."""
        response = requests.post(self.TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": integration.refresh_token,
            "grant_type": "refresh_token",
        })
        response.raise_for_status()
        data = response.json()

        integration.access_token = data["access_token"]
        integration.token_expires_at = timezone.now() + timedelta(
            seconds=data.get("expires_in", 3600)
        )
        integration.save(update_fields=["access_token", "token_expires_at"])

        return data["access_token"]

    def get_access_token(self, integration: CalendarIntegration) -> str:
        """Get a valid access token, refreshing if necessary."""
        if integration.is_token_expired:
            return self.refresh_access_token(integration)
        return integration.access_token

    def list_calendars(self, integration: CalendarIntegration) -> list:
        """List all calendars for the connected Google account."""
        token = self.get_access_token(integration)
        response = requests.get(
            f"{self.CALENDAR_API}/users/me/calendarList",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return [
            {
                "id": cal["id"],
                "name": cal["summary"],
                "primary": cal.get("primary", False),
                "color": cal.get("backgroundColor", "#3B82F6"),
            }
            for cal in response.json().get("items", [])
        ]

    def get_events(
        self,
        integration: CalendarIntegration,
        time_min: datetime,
        time_max: datetime,
    ) -> list:
        """Fetch events from Google Calendar within a time range."""
        token = self.get_access_token(integration)
        calendar_id = integration.external_calendar_id or "primary"

        response = requests.get(
            f"{self.CALENDAR_API}/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 250,
            },
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def create_event(self, integration: CalendarIntegration, booking) -> str:
        """Create a Google Calendar event from a booking."""
        token = self.get_access_token(integration)
        calendar_id = integration.external_calendar_id or "primary"

        event_body = {
            "summary": f"Meeting with {booking.invitee_name}",
            "description": (
                f"Booking: {booking.reference}\n"
                f"Event Type: {booking.event_type.name if booking.event_type else 'Meeting'}\n"
                f"Invitee: {booking.invitee_name} ({booking.invitee_email})"
            ),
            "start": {
                "dateTime": booking.start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": booking.end_time.isoformat(),
                "timeZone": "UTC",
            },
            "attendees": [
                {"email": booking.invitee_email, "displayName": booking.invitee_name},
            ],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "popup", "minutes": 15},
                ],
            },
        }

        if booking.meeting_link:
            event_body["conferenceData"] = {
                "entryPoints": [{
                    "entryPointType": "video",
                    "uri": booking.meeting_link,
                }],
            }

        response = requests.post(
            f"{self.CALENDAR_API}/calendars/{calendar_id}/events",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=event_body,
        )
        response.raise_for_status()
        return response.json()["id"]


class CalendarSyncService:
    """Orchestrates sync across all connected calendar providers."""

    def sync_all_connected_calendars(self) -> dict:
        """Sync all active calendar integrations."""
        integrations = CalendarIntegration.objects.filter(
            is_active=True,
            sync_status="active",
        ).select_related("user")

        synced = 0
        errors = 0

        for integration in integrations:
            try:
                self.sync_integration(integration)
                synced += 1
            except Exception as exc:
                errors += 1
                integration.last_sync_error = str(exc)
                integration.sync_status = "error"
                integration.save(update_fields=["last_sync_error", "sync_status"])
                logger.error(
                    "Sync failed for %s (%s): %s",
                    integration.provider,
                    integration.user.email,
                    str(exc),
                )

        return {"synced": synced, "errors": errors}

    def sync_integration(self, integration: CalendarIntegration):
        """Sync a single calendar integration."""
        if integration.provider == "google":
            service = GoogleCalendarService()
            events = service.get_events(
                integration,
                time_min=timezone.now(),
                time_max=timezone.now() + timedelta(days=60),
            )
            logger.info(
                "Synced %d events from Google Calendar for %s",
                len(events),
                integration.user.email,
            )
        integration.last_synced_at = timezone.now()
        integration.save(update_fields=["last_synced_at"])

    def sync_booking(self, booking):
        """Sync a specific booking to all connected calendars."""
        integrations = CalendarIntegration.objects.filter(
            user=booking.host,
            is_active=True,
            sync_status="active",
            sync_direction__in=["both", "export_only"],
        )

        for integration in integrations:
            if integration.provider == "google":
                service = GoogleCalendarService()
                try:
                    event_id = service.create_event(integration, booking)
                    booking.google_event_id = event_id
                    booking.save(update_fields=["google_event_id"])
                    logger.info(
                        "Created Google Calendar event %s for booking %s",
                        event_id,
                        booking.reference,
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to sync booking %s to Google: %s",
                        booking.reference,
                        str(exc),
                    )


class WebhookDeliveryService:
    """Delivers webhook payloads to registered endpoints."""

    def deliver(self, event_type: str, payload: dict, user):
        """Send webhook event to all matching endpoints for a user."""
        endpoints = WebhookEndpoint.objects.filter(
            user=user,
            is_active=True,
        )

        for endpoint in endpoints:
            if event_type in endpoint.events:
                self._send_webhook(endpoint, event_type, payload)

    def _send_webhook(self, endpoint: WebhookEndpoint, event_type: str, payload: dict):
        """Send a single webhook delivery."""
        body = json.dumps({
            "event": event_type,
            "timestamp": timezone.now().isoformat(),
            "data": payload,
        })

        signature = hmac.new(
            endpoint.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-BookingEngine-Event": event_type,
            "X-BookingEngine-Signature": f"sha256={signature}",
        }

        try:
            response = requests.post(
                endpoint.url,
                data=body,
                headers=headers,
                timeout=10,
            )
            endpoint.total_deliveries += 1
            endpoint.last_delivery_at = timezone.now()
            endpoint.last_response_code = response.status_code

            if response.status_code >= 400:
                endpoint.total_failures += 1
                endpoint.last_failure_at = timezone.now()

            endpoint.save(update_fields=[
                "total_deliveries", "total_failures",
                "last_delivery_at", "last_failure_at",
                "last_response_code",
            ])

        except requests.RequestException as exc:
            endpoint.total_deliveries += 1
            endpoint.total_failures += 1
            endpoint.last_failure_at = timezone.now()
            endpoint.save(update_fields=[
                "total_deliveries", "total_failures", "last_failure_at",
            ])
            logger.error("Webhook delivery to %s failed: %s", endpoint.url, str(exc))
