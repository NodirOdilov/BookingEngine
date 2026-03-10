"""
Timezone utility functions for BookingEngine.
Handles timezone conversions, available slots computation, and overlap detection.
"""

import pytz
from datetime import datetime, time, timedelta
from typing import Optional

from django.utils import timezone


# Common timezone choices grouped by region
TIMEZONE_CHOICES = [
    ("US & Canada", [
        ("America/New_York", "Eastern Time (US & Canada)"),
        ("America/Chicago", "Central Time (US & Canada)"),
        ("America/Denver", "Mountain Time (US & Canada)"),
        ("America/Los_Angeles", "Pacific Time (US & Canada)"),
        ("America/Anchorage", "Alaska"),
        ("Pacific/Honolulu", "Hawaii"),
    ]),
    ("Europe", [
        ("Europe/London", "London"),
        ("Europe/Paris", "Paris"),
        ("Europe/Berlin", "Berlin"),
        ("Europe/Moscow", "Moscow"),
        ("Europe/Istanbul", "Istanbul"),
    ]),
    ("Asia", [
        ("Asia/Dubai", "Dubai"),
        ("Asia/Kolkata", "Kolkata"),
        ("Asia/Bangkok", "Bangkok"),
        ("Asia/Shanghai", "Shanghai"),
        ("Asia/Tokyo", "Tokyo"),
        ("Asia/Seoul", "Seoul"),
    ]),
    ("Pacific", [
        ("Australia/Sydney", "Sydney"),
        ("Australia/Melbourne", "Melbourne"),
        ("Pacific/Auckland", "Auckland"),
    ]),
]

FLAT_TIMEZONE_CHOICES = [
    (tz, label)
    for _group, tzs in TIMEZONE_CHOICES
    for tz, label in tzs
]


def get_all_timezones():
    """Return all valid IANA timezone identifiers."""
    return pytz.all_timezones


def convert_to_timezone(dt: datetime, target_tz: str) -> datetime:
    """Convert a datetime to a specified timezone."""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    target = pytz.timezone(target_tz)
    return dt.astimezone(target)


def get_current_time_in_tz(tz_str: str) -> datetime:
    """Get the current time in a specified timezone."""
    tz = pytz.timezone(tz_str)
    return timezone.now().astimezone(tz)


def make_aware_in_tz(naive_dt: datetime, tz_str: str) -> datetime:
    """Make a naive datetime aware in the specified timezone."""
    tz = pytz.timezone(tz_str)
    return tz.localize(naive_dt)


def combine_date_time_tz(
    date_val,
    time_val: time,
    tz_str: str,
) -> datetime:
    """Combine a date and time into a timezone-aware datetime."""
    naive = datetime.combine(date_val, time_val)
    return make_aware_in_tz(naive, tz_str)


def get_day_boundaries(
    date_val,
    tz_str: str,
) -> tuple[datetime, datetime]:
    """Get the start and end of a day in a given timezone, as UTC."""
    start = combine_date_time_tz(date_val, time.min, tz_str)
    end = combine_date_time_tz(date_val, time.max, tz_str)
    return start.astimezone(pytz.UTC), end.astimezone(pytz.UTC)


def generate_time_slots(
    start_time: time,
    end_time: time,
    duration_minutes: int,
    buffer_before: int = 0,
    buffer_after: int = 0,
) -> list[tuple[time, time]]:
    """
    Generate time slots within a window, accounting for buffer times.

    Returns a list of (slot_start, slot_end) tuples.
    """
    slots = []
    total_slot_minutes = buffer_before + duration_minutes + buffer_after

    current = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    while current + timedelta(minutes=total_slot_minutes) <= end:
        slot_start = (current + timedelta(minutes=buffer_before)).time()
        slot_end = (current + timedelta(minutes=buffer_before + duration_minutes)).time()
        slots.append((slot_start, slot_end))
        current += timedelta(minutes=total_slot_minutes)

    return slots


def do_time_ranges_overlap(
    start1: datetime,
    end1: datetime,
    start2: datetime,
    end2: datetime,
) -> bool:
    """Check if two time ranges overlap."""
    return start1 < end2 and start2 < end1


def is_within_notice_period(
    slot_start: datetime,
    minimum_notice_hours: int,
    reference_time: Optional[datetime] = None,
) -> bool:
    """Check if a time slot is within the minimum notice period."""
    if reference_time is None:
        reference_time = timezone.now()
    notice_cutoff = reference_time + timedelta(hours=minimum_notice_hours)
    return slot_start >= notice_cutoff


def get_week_date_range(date_val, tz_str: str = "UTC"):
    """Get Monday-Sunday date range for the week containing the given date."""
    weekday = date_val.weekday()
    monday = date_val - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def validate_timezone(tz_str: str) -> bool:
    """Check if a timezone string is valid."""
    try:
        pytz.timezone(tz_str)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False
