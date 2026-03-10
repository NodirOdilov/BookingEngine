"""
URL configuration for notifications app.
Note: Notification endpoints are included as part of the settings/user preferences
rather than a separate API prefix. This module exists for app consistency.
"""

from django.urls import path

from .views import NotificationLogViewSet, NotificationPreferenceView
from rest_framework.routers import DefaultRouter
from django.urls import include

router = DefaultRouter()
router.register(r"logs", NotificationLogViewSet, basename="notification-log")

urlpatterns = [
    path(
        "preferences/",
        NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
    path("", include(router.urls)),
]
