"""
Notification service for BookingEngine.
Handles email sending, template rendering, and notification dispatch.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NotificationLog, NotificationTemplate, UserNotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """Central service for sending all types of notifications."""

    def send_booking_created(self, booking):
        """Send notification when a new booking is created."""
        context = self._build_booking_context(booking)

        # Notify host
        if self._should_notify(booking.host, "email_new_booking"):
            self._send_templated_email(
                template_type="booking_created",
                recipient_type="host",
                to_email=booking.host.email,
                to_name=booking.host.full_name,
                context=context,
                booking=booking,
                user=booking.host,
            )

        # Notify invitee
        self._send_templated_email(
            template_type="booking_created",
            recipient_type="invitee",
            to_email=booking.invitee_email,
            to_name=booking.invitee_name,
            context=context,
            booking=booking,
        )

    def send_booking_confirmed(self, booking):
        """Send notification when a booking is confirmed."""
        context = self._build_booking_context(booking)

        self._send_templated_email(
            template_type="booking_confirmed",
            recipient_type="invitee",
            to_email=booking.invitee_email,
            to_name=booking.invitee_name,
            context=context,
            booking=booking,
        )

    def send_booking_cancelled(self, booking):
        """Send cancellation notification to both parties."""
        context = self._build_booking_context(booking)
        context["cancellation_reason"] = booking.get_cancellation_reason_display()

        if self._should_notify(booking.host, "email_booking_cancelled"):
            self._send_templated_email(
                template_type="booking_cancelled",
                recipient_type="host",
                to_email=booking.host.email,
                to_name=booking.host.full_name,
                context=context,
                booking=booking,
                user=booking.host,
            )

        self._send_templated_email(
            template_type="booking_cancelled",
            recipient_type="invitee",
            to_email=booking.invitee_email,
            to_name=booking.invitee_name,
            context=context,
            booking=booking,
        )

    def send_booking_rescheduled(self, booking, old_start, old_end):
        """Send rescheduling notification."""
        context = self._build_booking_context(booking)
        context["old_start_time"] = old_start.isoformat()
        context["old_end_time"] = old_end.isoformat()

        if self._should_notify(booking.host, "email_booking_rescheduled"):
            self._send_templated_email(
                template_type="booking_rescheduled",
                recipient_type="host",
                to_email=booking.host.email,
                to_name=booking.host.full_name,
                context=context,
                booking=booking,
                user=booking.host,
            )

        self._send_templated_email(
            template_type="booking_rescheduled",
            recipient_type="invitee",
            to_email=booking.invitee_email,
            to_name=booking.invitee_name,
            context=context,
            booking=booking,
        )

    def send_reminder(self, to_email, to_name, booking, channel="email"):
        """Send a booking reminder."""
        context = self._build_booking_context(booking)

        if channel == "email":
            self._send_templated_email(
                template_type="booking_reminder",
                recipient_type="invitee" if to_email == booking.invitee_email else "host",
                to_email=to_email,
                to_name=to_name,
                context=context,
                booking=booking,
            )
        elif channel == "sms":
            logger.info("SMS reminder would be sent to %s", to_email)

    def send_daily_digest(self, user):
        """Send a daily digest of upcoming bookings."""
        from apps.bookings.models import Booking

        now = timezone.now()
        tomorrow = now + timedelta(days=1)

        upcoming = Booking.objects.filter(
            host=user,
            start_time__date=tomorrow.date(),
            status="confirmed",
        ).order_by("start_time")

        if not upcoming.exists():
            return

        context = {
            "user_name": user.full_name,
            "date": tomorrow.date().isoformat(),
            "booking_count": upcoming.count(),
            "bookings": [
                {
                    "reference": b.reference,
                    "invitee_name": b.invitee_name,
                    "start_time": b.start_time.isoformat(),
                    "duration": b.duration,
                    "event_type": b.event_type.name if b.event_type else "Meeting",
                }
                for b in upcoming
            ],
            "frontend_url": settings.FRONTEND_URL,
        }

        self._send_templated_email(
            template_type="daily_digest",
            recipient_type="host",
            to_email=user.email,
            to_name=user.full_name,
            context=context,
            user=user,
        )

    def _build_booking_context(self, booking):
        """Build common template context for booking notifications."""
        return {
            "booking_reference": booking.reference,
            "host_name": booking.host.full_name,
            "host_email": booking.host.email,
            "invitee_name": booking.invitee_name,
            "invitee_email": booking.invitee_email,
            "event_type_name": booking.event_type.name if booking.event_type else "Meeting",
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "duration": booking.duration,
            "location_type": booking.location_type,
            "location_detail": booking.location_detail,
            "meeting_link": booking.meeting_link,
            "status": booking.get_status_display(),
            "manage_url": f"{settings.FRONTEND_URL}/bookings/{booking.reference}",
            "cancel_url": f"{settings.FRONTEND_URL}/bookings/{booking.reference}/cancel",
            "reschedule_url": f"{settings.FRONTEND_URL}/bookings/{booking.reference}/reschedule",
            "frontend_url": settings.FRONTEND_URL,
        }

    def _send_templated_email(
        self,
        template_type,
        recipient_type,
        to_email,
        to_name,
        context,
        booking=None,
        user=None,
    ):
        """Send an email using a notification template."""
        template = self._get_template(template_type, recipient_type)

        if template:
            subject, html_body, text_body = template.render(context)
        else:
            subject = f"BookingEngine: {template_type.replace('_', ' ').title()}"
            html_body = f"<p>Notification: {template_type}</p>"
            text_body = f"Notification: {template_type}"

        # Log the notification
        log = NotificationLog.objects.create(
            user=user,
            booking=booking,
            channel="email",
            notification_type=template_type,
            recipient_email=to_email,
            recipient_name=to_name,
            subject=subject,
            body_preview=text_body[:500] if text_body else html_body[:500],
            status="queued",
        )

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body or "Please view this email in an HTML-capable client.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            if html_body:
                email.attach_alternative(html_body, "text/html")
            email.send()

            log.status = "sent"
            log.sent_at = timezone.now()
            log.save(update_fields=["status", "sent_at"])

            logger.info("Sent %s email to %s", template_type, to_email)

        except Exception as exc:
            log.status = "failed"
            log.error_message = str(exc)
            log.save(update_fields=["status", "error_message"])
            logger.error("Failed to send %s email to %s: %s", template_type, to_email, exc)

    def _get_template(self, template_type, recipient_type):
        """Retrieve the appropriate notification template."""
        return NotificationTemplate.objects.filter(
            template_type=template_type,
            recipient_type=recipient_type,
            is_active=True,
        ).first()

    def _should_notify(self, user, preference_field):
        """Check if a user should receive a specific notification type."""
        try:
            prefs = user.notification_preferences
            return getattr(prefs, preference_field, True)
        except UserNotificationPreference.DoesNotExist:
            return True
