"""
URL configuration for event_types app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EventTypeViewSet,
    PublicEventTypeDetailView,
    PublicEventTypeListView,
)

router = DefaultRouter()
router.register(r"", EventTypeViewSet, basename="event-type")

urlpatterns = [
    # Public event type endpoints
    path(
        "public/<slug:user_slug>/",
        PublicEventTypeListView.as_view(),
        name="public-event-type-list",
    ),
    path(
        "public/<slug:user_slug>/<slug:slug>/",
        PublicEventTypeDetailView.as_view(),
        name="public-event-type-detail",
    ),
    # Authenticated CRUD
    path("", include(router.urls)),
]
