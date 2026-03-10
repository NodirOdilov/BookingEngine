"""
Celery tasks for notifications app.
Handles asynchronous email sending and digest emails.
"""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_notification(self, booking_id, notification_type):
    """
    Send a notification for a booking event.

    Args:
        booking_id: UUID of the booking
        notification_type: One of 'created', 'confirmed', 'cancelled', 'rescheduled'
    """
    from apps.bookings.models import Booking
    from .services import NotificationService

    try:
        booking = Booking.objects.select_related(
            "host", "event_type", "calendar"
        ).get(id=booking_id)
    except Booking.DoesNotExist:
        logger.error("Booking %s not found for notification", booking_id)
        return

    service = NotificationService()

    handlers = {
        "created": service.send_booking_created,
        "confirmed": service.send_booking_confirmed,
        "cancelled": service.send_booking_cancelled,
    }

    handler = handlers.get(notification_type)
    if handler:
        try:
            handler(booking)
            logger.info(
                "Sent %s notification for booking %s",
                notification_type,
                booking.reference,
            )
        except Exception as exc:
            logger.error(
                "Failed to send %s notification for booking %s: %s",
                notification_type,
                booking.reference,
                str(exc),
            )
            self.retry(exc=exc)
    else:
        logger.warning("Unknown notification type: %s", notification_type)


@shared_task(bind=True, max_retries=2)
def send_daily_digest(self):
    """
    Send daily digest emails to all users who have it enabled.
    Runs daily at 7 AM via Celery Beat.
    """
    from .models import UserNotificationPreference
    from .services import NotificationService

    service = NotificationService()

    # Get users who want daily digest
    users_with_digest = User.objects.filter(
        is_active=True,
        notification_preferences__email_daily_digest=True,
    ).select_related("notification_preferences")

    # Fallback: include users without preferences (default is True)
    users_without_prefs = User.objects.filter(
        is_active=True,
    ).exclude(
        id__in=UserNotificationPreference.objects.values_list("user_id", flat=True)
    )

    sent_count = 0
    for user in list(users_with_digest) + list(users_without_prefs):
        try:
            service.send_daily_digest(user)
            sent_count += 1
        except Exception as exc:
            logger.error("Failed to send digest to %s: %s", user.email, str(exc))

    logger.info("Sent %d daily digest emails", sent_count)
    return {"sent": sent_count}


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """Send a welcome email to a newly registered user."""
    from .services import NotificationService

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("User %s not found for welcome email", user_id)
        return

    service = NotificationService()
    service._send_templated_email(
        template_type="welcome",
        recipient_type="host",
        to_email=user.email,
        to_name=user.full_name,
        context={
            "user_name": user.full_name,
            "frontend_url": "http://localhost:3000",
        },
        user=user,
    )
    logger.info("Sent welcome email to %s", user.email)
