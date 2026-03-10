"""
Views for notifications app: logs, templates, preferences.
"""

from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response

from .models import NotificationLog, NotificationTemplate, UserNotificationPreference
from .serializers import (
    NotificationLogSerializer,
    NotificationTemplateSerializer,
    UserNotificationPreferenceSerializer,
)


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to the authenticated user's notification history."""

    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = NotificationLog.objects.filter(user=self.request.user)

        channel = self.request.query_params.get("channel")
        if channel:
            qs = qs.filter(channel=channel)

        notification_type = self.request.query_params.get("type")
        if notification_type:
            qs = qs.filter(notification_type=notification_type)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's notification preferences."""

    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        prefs, created = UserNotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return prefs
