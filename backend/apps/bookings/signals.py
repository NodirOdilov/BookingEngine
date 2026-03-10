"""
Signals for bookings app.
Handles post-booking actions: notifications, calendar sync, time slot updates.
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Booking

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Booking)
def track_status_change(sender, instance, **kwargs):
    """Track when booking status changes for triggering notifications."""
    if instance.pk:
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Booking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Booking)
def handle_booking_saved(sender, instance, created, **kwargs):
    """
    Handle actions after a booking is saved.
    Dispatches notifications based on status changes.
    """
    if created:
        logger.info("New booking created: %s", instance.reference)
        _send_booking_confirmation_task(instance)
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status and old_status != instance.status:
        logger.info(
            "Booking %s status changed: %s -> %s",
            instance.reference,
            old_status,
            instance.status,
        )

        if instance.status == "confirmed" and old_status == "pending":
            _send_booking_confirmed_task(instance)
        elif instance.status == "cancelled":
            _send_booking_cancelled_task(instance)
        elif instance.status == "rescheduled":
            _send_booking_rescheduled_task(instance)


def _send_booking_confirmation_task(booking):
    """Queue booking confirmation notification."""
    try:
        from apps.notifications.tasks import send_booking_notification
        send_booking_notification.delay(str(booking.id), "created")
    except ImportError:
        logger.warning("Notifications app not available for booking %s", booking.reference)


def _send_booking_confirmed_task(booking):
    """Queue booking confirmed notification."""
    try:
        from apps.notifications.tasks import send_booking_notification
        send_booking_notification.delay(str(booking.id), "confirmed")
    except ImportError:
        logger.warning("Notifications app not available for booking %s", booking.reference)


def _send_booking_cancelled_task(booking):
    """Queue booking cancelled notification."""
    try:
        from apps.notifications.tasks import send_booking_notification
        send_booking_notification.delay(str(booking.id), "cancelled")
    except ImportError:
        logger.warning("Notifications app not available for booking %s", booking.reference)


def _send_booking_rescheduled_task(booking):
    """Queue booking rescheduled notification."""
    try:
        from apps.notifications.tasks import send_booking_notification
        send_booking_notification.delay(str(booking.id), "rescheduled")
    except ImportError:
        logger.warning("Notifications app not available for booking %s", booking.reference)
