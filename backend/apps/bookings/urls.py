"""
URL configuration for bookings app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingViewSet,
    PublicBookingCancelView,
    PublicBookingCreateView,
    PublicBookingDetailView,
    PublicBookingRescheduleView,
)

router = DefaultRouter()
router.register(r"", BookingViewSet, basename="booking")

urlpatterns = [
    # Public booking endpoints (no auth required)
    path("public/create/", PublicBookingCreateView.as_view(), name="public-booking-create"),
    path(
        "public/<str:reference>/",
        PublicBookingDetailView.as_view(),
        name="public-booking-detail",
    ),
    path(
        "public/<str:reference>/cancel/",
        PublicBookingCancelView.as_view(),
        name="public-booking-cancel",
    ),
    path(
        "public/<str:reference>/reschedule/",
        PublicBookingRescheduleView.as_view(),
        name="public-booking-reschedule",
    ),
    # Authenticated booking management
    path("", include(router.urls)),
]
