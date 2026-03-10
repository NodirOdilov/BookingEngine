"""
Views for booking_pages app: booking page management, embed widgets, public pages.
"""

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.event_types.models import EventType
from apps.event_types.serializers import EventTypePublicSerializer
from .models import BookingPage, EmbedWidget
from .serializers import (
    BookingPagePublicSerializer,
    BookingPageSerializer,
    BookingPageUpdateSerializer,
    EmbedWidgetSerializer,
)


class BookingPageViewSet(viewsets.ModelViewSet):
    """CRUD operations for booking pages."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return BookingPageUpdateSerializer
        return BookingPageSerializer

    def get_queryset(self):
        return BookingPage.objects.filter(
            user=self.request.user
        ).select_related("user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmbedWidgetViewSet(viewsets.ModelViewSet):
    """CRUD operations for embed widgets."""

    serializer_class = EmbedWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmbedWidget.objects.filter(
            user=self.request.user
        ).select_related("event_type")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="track-view")
    def track_view(self, request, pk=None):
        """Increment the view counter for a widget."""
        widget = self.get_object()
        widget.total_views += 1
        widget.save(update_fields=["total_views"])
        return Response({"total_views": widget.total_views})


class PublicBookingPageView(generics.RetrieveAPIView):
    """
    Public endpoint to retrieve a user's booking page.
    Looked up by user slug.
    """

    serializer_class = BookingPagePublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        user_slug = self.kwargs["user_slug"]
        return BookingPage.objects.select_related("user").get(
            user__slug=user_slug,
            is_active=True,
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except BookingPage.DoesNotExist:
            return Response(
                {"detail": "Booking page not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        page_data = BookingPagePublicSerializer(page).data

        # Include event types available on the page
        event_types = EventType.objects.filter(
            user=page.user,
            is_active=True,
            is_secret=False,
        ).select_related("user").prefetch_related("locations")

        page_data["event_types"] = EventTypePublicSerializer(
            event_types, many=True
        ).data

        return Response(page_data)


class EmbedBookingView(generics.RetrieveAPIView):
    """
    Public endpoint for embedded booking widgets.
    Returns event type and booking page data for the embed.
    """

    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        token = self.kwargs["embed_token"]
        try:
            widget = EmbedWidget.objects.select_related(
                "event_type", "event_type__user"
            ).get(embed_token=token, is_active=True)
        except EmbedWidget.DoesNotExist:
            return Response(
                {"detail": "Widget not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Track the view
        widget.total_views += 1
        widget.save(update_fields=["total_views"])

        event_type = widget.event_type
        return Response({
            "event_type": EventTypePublicSerializer(event_type).data,
            "widget": EmbedWidgetSerializer(widget).data,
        })
