"""
URL configuration for calendars app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AvailabilityRuleDetailView,
    BlockedTimeDetailView,
    CalendarViewSet,
)

router = DefaultRouter()
router.register(r"", CalendarViewSet, basename="calendar")

urlpatterns = [
    path(
        "availability-rules/<uuid:pk>/",
        AvailabilityRuleDetailView.as_view(),
        name="availability-rule-detail",
    ),
    path(
        "blocked-times/<uuid:pk>/",
        BlockedTimeDetailView.as_view(),
        name="blocked-time-detail",
    ),
    path("", include(router.urls)),
]
