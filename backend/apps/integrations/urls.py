"""
URL configuration for integrations app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CalendarIntegrationViewSet,
    WebhookEndpointViewSet,
    google_oauth_callback,
)

router = DefaultRouter()
router.register(r"calendars", CalendarIntegrationViewSet, basename="calendar-integration")
router.register(r"webhooks", WebhookEndpointViewSet, basename="webhook-endpoint")

urlpatterns = [
    path("google/callback/", google_oauth_callback, name="google-oauth-callback"),
    path("", include(router.urls)),
]
