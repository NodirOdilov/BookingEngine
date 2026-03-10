"""
Celery configuration for BookingEngine.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("bookingengine")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks([
    "apps.bookings",
    "apps.notifications",
])

app.conf.beat_schedule = {
    "send-booking-reminders-every-5-minutes": {
        "task": "apps.bookings.tasks.send_upcoming_reminders",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-expired-pending-bookings": {
        "task": "apps.bookings.tasks.cleanup_expired_bookings",
        "schedule": crontab(minute="*/15"),
    },
    "sync-external-calendars": {
        "task": "apps.bookings.tasks.sync_all_external_calendars",
        "schedule": crontab(minute="*/10"),
    },
    "send-daily-digest": {
        "task": "apps.notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=7, minute=0),
    },
}

app.conf.task_routes = {
    "apps.notifications.*": {"queue": "notifications"},
    "apps.bookings.*": {"queue": "bookings"},
    "apps.payments.*": {"queue": "payments"},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
