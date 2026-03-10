"""
Views for bookings app: CRUD, reschedule, cancel, public booking, host dashboard.
"""

from datetime import timedelta

from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Booking, BookingNote, RescheduleHistory
from .serializers import (
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingListSerializer,
    BookingNoteSerializer,
    BookingPublicSerializer,
    BookingRescheduleSerializer,
    BookingSerializer,
)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    Hosts can view, update status, add notes, and manage their bookings.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "calendar", "event_type"]
    search_fields = ["invitee_name", "invitee_email", "reference"]
    ordering_fields = ["start_time", "created_at", "status"]
    ordering = ["-start_time"]

    def get_serializer_class(self):
        if self.action == "list":
            return BookingListSerializer
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        qs = Booking.objects.filter(
            host=self.request.user
        ).select_related("event_type", "calendar", "host", "invitee")

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            qs = qs.filter(start_time__date__gte=start_date)
        if end_date:
            qs = qs.filter(start_time__date__lte=end_date)

        # Filter upcoming/past
        time_filter = self.request.query_params.get("time_filter")
        if time_filter == "upcoming":
            qs = qs.filter(
                start_time__gt=timezone.now(),
                status__in=["confirmed", "pending"],
            )
        elif time_filter == "past":
            qs = qs.filter(end_time__lt=timezone.now())

        return qs

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a pending booking."""
        booking = self.get_object()
        if booking.status != "pending":
            return Response(
                {"detail": "Only pending bookings can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.confirm()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        if not booking.can_cancel:
            return Response(
                {"detail": "This booking cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking.cancel(
            reason=serializer.validated_data.get("reason", "host_cancelled"),
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        """Reschedule a booking to a new time."""
        booking = self.get_object()
        if not booking.can_reschedule:
            return Response(
                {"detail": "This booking cannot be rescheduled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BookingRescheduleSerializer(
            data=request.data,
            context={"booking": booking},
        )
        serializer.is_valid(raise_exception=True)

        new_start = serializer.validated_data["new_start_time"]
        new_end = new_start + timedelta(minutes=booking.duration)
        reason = serializer.validated_data.get("reason", "")

        # Save reschedule history
        RescheduleHistory.objects.create(
            booking=booking,
            previous_start=booking.start_time,
            previous_end=booking.end_time,
            new_start=new_start,
            new_end=new_end,
            rescheduled_by=request.user,
            rescheduled_by_email=request.user.email,
            reason=reason,
        )

        booking.start_time = new_start
        booking.end_time = new_end
        booking.status = "confirmed"
        booking.save(update_fields=["start_time", "end_time", "status", "updated_at"])

        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="mark-completed")
    def mark_completed(self, request, pk=None):
        """Mark a booking as completed."""
        booking = self.get_object()
        if booking.status != "confirmed":
            return Response(
                {"detail": "Only confirmed bookings can be marked completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.mark_completed()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="mark-no-show")
    def mark_no_show(self, request, pk=None):
        """Mark a booking as no-show."""
        booking = self.get_object()
        if booking.status != "confirmed":
            return Response(
                {"detail": "Only confirmed bookings can be marked as no-show."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.mark_no_show()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["get", "post"])
    def notes(self, request, pk=None):
        """List or add notes to a booking."""
        booking = self.get_object()

        if request.method == "GET":
            notes = BookingNote.objects.filter(booking=booking)
            serializer = BookingNoteSerializer(notes, many=True)
            return Response(serializer.data)

        serializer = BookingNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(booking=booking, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get booking statistics for the dashboard."""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        base_qs = Booking.objects.filter(host=request.user)

        return Response({
            "upcoming_count": base_qs.filter(
                start_time__gt=now, status="confirmed"
            ).count(),
            "today_count": base_qs.filter(
                start_time__date=today_start.date(), status="confirmed"
            ).count(),
            "pending_count": base_qs.filter(status="pending").count(),
            "week_count": base_qs.filter(
                start_time__gte=week_start,
                start_time__lt=week_start + timedelta(days=7),
                status__in=["confirmed", "completed"],
            ).count(),
            "month_count": base_qs.filter(
                start_time__gte=month_start,
                status__in=["confirmed", "completed"],
            ).count(),
            "cancellation_rate": self._cancellation_rate(base_qs, month_start),
            "no_show_rate": self._no_show_rate(base_qs, month_start),
        })

    def _cancellation_rate(self, qs, since):
        total = qs.filter(created_at__gte=since).count()
        if total == 0:
            return 0
        cancelled = qs.filter(created_at__gte=since, status="cancelled").count()
        return round(cancelled / total * 100, 1)

    def _no_show_rate(self, qs, since):
        total = qs.filter(created_at__gte=since, status__in=["completed", "no_show"]).count()
        if total == 0:
            return 0
        no_shows = qs.filter(created_at__gte=since, status="no_show").count()
        return round(no_shows / total * 100, 1)


class PublicBookingCreateView(generics.CreateAPIView):
    """
    Public endpoint for invitees to create bookings.
    No authentication required.
    """

    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        return Response(
            BookingPublicSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class PublicBookingDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view booking details by reference code.
    Used on confirmation and management pages.
    """

    serializer_class = BookingPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "reference"
    queryset = Booking.objects.all()


class PublicBookingCancelView(generics.UpdateAPIView):
    """Public endpoint for invitees to cancel their booking."""

    serializer_class = BookingCancelSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "reference"
    queryset = Booking.objects.all()

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if not booking.can_cancel:
            return Response(
                {"detail": "This booking cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking.cancel(
            reason=serializer.validated_data.get("reason", "invitee_cancelled"),
            notes=serializer.validated_data.get("notes", ""),
        )

        return Response(BookingPublicSerializer(booking).data)


class PublicBookingRescheduleView(generics.UpdateAPIView):
    """Public endpoint for invitees to reschedule their booking."""

    serializer_class = BookingRescheduleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "reference"
    queryset = Booking.objects.all()

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if not booking.can_reschedule:
            return Response(
                {"detail": "This booking cannot be rescheduled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={"booking": booking},
        )
        serializer.is_valid(raise_exception=True)

        new_start = serializer.validated_data["new_start_time"]
        new_end = new_start + timedelta(minutes=booking.duration)
        reason = serializer.validated_data.get("reason", "")

        RescheduleHistory.objects.create(
            booking=booking,
            previous_start=booking.start_time,
            previous_end=booking.end_time,
            new_start=new_start,
            new_end=new_end,
            rescheduled_by_email=booking.invitee_email,
            reason=reason,
        )

        booking.start_time = new_start
        booking.end_time = new_end
        booking.save(update_fields=["start_time", "end_time", "updated_at"])

        return Response(BookingPublicSerializer(booking).data)
