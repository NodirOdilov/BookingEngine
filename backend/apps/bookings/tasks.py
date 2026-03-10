"""
Celery tasks for bookings app.
Handles reminders, cleanup, and external calendar sync.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_upcoming_reminders(self):
    """
    Check for upcoming bookings and send reminders.
    Runs every 5 minutes via Celery Beat.
    """
    from .models import BookingReminder

    now = timezone.now()
    pending_reminders = BookingReminder.objects.filter(
        is_sent=False,
        scheduled_at__lte=now,
        booking__status="confirmed",
    ).select_related("booking", "booking__host")

    sent_count = 0
    for reminder in pending_reminders[:50]:  # Process in batches
        try:
            _dispatch_reminder(reminder)
            reminder.is_sent = True
            reminder.sent_at = now
            reminder.save(update_fields=["is_sent", "sent_at"])
            sent_count += 1
        except Exception as exc:
            logger.error(
                "Failed to send reminder %s: %s",
                reminder.id,
                str(exc),
            )
            reminder.error_message = str(exc)
            reminder.save(update_fields=["error_message"])

    if sent_count > 0:
        logger.info("Sent %d booking reminders", sent_count)

    return {"sent": sent_count}


def _dispatch_reminder(reminder):
    """Send a single reminder based on its type and recipient."""
    from apps.notifications.services import NotificationService

    booking = reminder.booking
    service = NotificationService()

    if reminder.recipient in ("host", "both"):
        service.send_reminder(
            to_email=booking.host.email,
            to_name=booking.host.full_name,
            booking=booking,
            channel=reminder.reminder_type,
        )

    if reminder.recipient in ("invitee", "both"):
        service.send_reminder(
            to_email=booking.invitee_email,
            to_name=booking.invitee_name,
            booking=booking,
            channel=reminder.reminder_type,
        )


@shared_task(bind=True, max_retries=2)
def cleanup_expired_bookings(self):
    """
    Cancel bookings that have been pending for too long.
    Runs every 15 minutes via Celery Beat.
    """
    from .models import Booking

    expiration_threshold = timezone.now() - timedelta(hours=24)

    expired = Booking.objects.filter(
        status="pending",
        created_at__lt=expiration_threshold,
    )

    count = expired.count()
    if count > 0:
        for booking in expired:
            booking.cancel(reason="system", notes="Auto-cancelled: confirmation timeout")
        logger.info("Cancelled %d expired pending bookings", count)

    return {"cancelled": count}


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_all_external_calendars(self):
    """
    Sync bookings with connected external calendars (Google, Outlook).
    Runs every 10 minutes via Celery Beat.
    """
    from apps.integrations.services import CalendarSyncService

    try:
        service = CalendarSyncService()
        result = service.sync_all_connected_calendars()
        logger.info(
            "Calendar sync completed: %d synced, %d errors",
            result.get("synced", 0),
            result.get("errors", 0),
        )
        return result
    except Exception as exc:
        logger.error("Calendar sync failed: %s", str(exc))
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def sync_booking_to_external_calendar(self, booking_id):
    """Sync a single booking to connected external calendars."""
    from .models import Booking
    from apps.integrations.services import CalendarSyncService

    try:
        booking = Booking.objects.get(id=booking_id)
        service = CalendarSyncService()
        service.sync_booking(booking)
        logger.info("Synced booking %s to external calendar", booking.reference)
    except Booking.DoesNotExist:
        logger.error("Booking %s not found for sync", booking_id)
    except Exception as exc:
        logger.error("Failed to sync booking %s: %s", booking_id, str(exc))
        self.retry(exc=exc)
