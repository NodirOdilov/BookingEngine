"""
URL configuration for booking_pages app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingPageViewSet,
    EmbedBookingView,
    EmbedWidgetViewSet,
    PublicBookingPageView,
)

router = DefaultRouter()
router.register(r"pages", BookingPageViewSet, basename="booking-page")
router.register(r"widgets", EmbedWidgetViewSet, basename="embed-widget")

urlpatterns = [
    # Public booking page
    path(
        "public/<slug:user_slug>/",
        PublicBookingPageView.as_view(),
        name="public-booking-page",
    ),
    # Embed endpoint
    path(
        "embed/<str:embed_token>/",
        EmbedBookingView.as_view(),
        name="embed-booking",
    ),
    # Authenticated management
    path("", include(router.urls)),
]
