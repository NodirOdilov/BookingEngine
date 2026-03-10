"""
Availability calculation service for BookingEngine.
Core engine that computes available time slots for a calendar, accounting for:
- Weekly availability rules
- Date-specific overrides
- Blocked times
- Existing bookings
- Buffer times
- Minimum notice periods
- Maximum bookings per day
"""

import logging
from datetime import datetime, date, time, timedelta
from typing import Optional

import pytz
from django.db.models import Q
from django.utils import timezone

from apps.bookings.models import Booking
from .models import AvailabilityRule, BlockedTime, Calendar

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Computes available time slots for a calendar."""

    def __init__(self, calendar: Calendar):
        self.calendar = calendar
        self.tz = pytz.timezone(calendar.timezone)

    def get_available_slots(
        self,
        target_date: date,
        duration_minutes: int = 30,
        invitee_tz: str = "UTC",
        event_type_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all available time slots for a given date.

        Returns a list of dicts:
        [
            {
                "start": "2025-01-15T09:00:00-05:00",
                "end": "2025-01-15T09:30:00-05:00",
                "start_utc": "2025-01-15T14:00:00+00:00",
                "end_utc": "2025-01-15T14:30:00+00:00",
            },
            ...
        ]
        """
        # Validate the date is within booking window
        now = timezone.now()
        today = now.astimezone(self.tz).date()

        if target_date < today:
            return []

        max_date = today + timedelta(days=self.calendar.max_days_ahead)
        if target_date > max_date:
            return []

        # Get availability windows for this date
        windows = self._get_availability_windows(target_date)
        if not windows:
            return []

        # Generate candidate slots from availability windows
        candidates = self._generate_candidate_slots(
            target_date, windows, duration_minutes
        )

        # Filter out blocked times
        candidates = self._filter_blocked_times(candidates, target_date)

        # Filter out existing bookings
        candidates = self._filter_existing_bookings(candidates, target_date)

        # Apply minimum notice
        candidates = self._filter_minimum_notice(candidates, now)

        # Apply max bookings per day
        candidates = self._filter_max_daily_bookings(candidates, target_date)

        # Convert to invitee timezone for display
        invitee_timezone = pytz.timezone(invitee_tz)
        result = []
        for slot_start, slot_end in candidates:
            result.append({
                "start": slot_start.astimezone(invitee_timezone).isoformat(),
                "end": slot_end.astimezone(invitee_timezone).isoformat(),
                "start_utc": slot_start.astimezone(pytz.UTC).isoformat(),
                "end_utc": slot_end.astimezone(pytz.UTC).isoformat(),
            })

        return result

    def _get_availability_windows(
        self, target_date: date
    ) -> list[tuple[time, time]]:
        """
        Get the availability windows for a specific date.
        Date overrides take priority over weekly rules.
        """
        # Check for date-specific overrides first
        overrides = AvailabilityRule.objects.filter(
            calendar=self.calendar,
            rule_type="date_override",
            specific_date=target_date,
        )

        if overrides.exists():
            windows = []
            for rule in overrides:
                if rule.is_available:
                    windows.append((rule.start_time, rule.end_time))
            return windows

        # Fall back to weekly rules
        day_of_week = target_date.weekday()
        weekly_rules = AvailabilityRule.objects.filter(
            calendar=self.calendar,
            rule_type="weekly",
            day_of_week=day_of_week,
            is_available=True,
        )

        return [(rule.start_time, rule.end_time) for rule in weekly_rules]

    def _generate_candidate_slots(
        self,
        target_date: date,
        windows: list[tuple[time, time]],
        duration_minutes: int,
    ) -> list[tuple[datetime, datetime]]:
        """Generate all possible time slots within availability windows."""
        candidates = []
        buffer_before = self.calendar.buffer_before
        buffer_after = self.calendar.buffer_after
        total_slot = buffer_before + duration_minutes + buffer_after

        for window_start, window_end in windows:
            current = self.tz.localize(
                datetime.combine(target_date, window_start)
            )
            end_boundary = self.tz.localize(
                datetime.combine(target_date, window_end)
            )

            while True:
                slot_start = current + timedelta(minutes=buffer_before)
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                full_end = slot_end + timedelta(minutes=buffer_after)

                if full_end > end_boundary:
                    break

                candidates.append((slot_start, slot_end))
                current += timedelta(minutes=total_slot)

        return candidates

    def _filter_blocked_times(
        self,
        candidates: list[tuple[datetime, datetime]],
        target_date: date,
    ) -> list[tuple[datetime, datetime]]:
        """Remove slots that overlap with blocked times."""
        if not candidates:
            return candidates

        day_start = self.tz.localize(datetime.combine(target_date, time.min))
        day_end = self.tz.localize(datetime.combine(target_date, time.max))

        blocked = BlockedTime.objects.filter(
            calendar=self.calendar,
            start_datetime__lt=day_end,
            end_datetime__gt=day_start,
        )

        if not blocked.exists():
            return candidates

        filtered = []
        for slot_start, slot_end in candidates:
            is_blocked = False
            for block in blocked:
                if slot_start < block.end_datetime and slot_end > block.start_datetime:
                    is_blocked = True
                    break
            if not is_blocked:
                filtered.append((slot_start, slot_end))

        return filtered

    def _filter_existing_bookings(
        self,
        candidates: list[tuple[datetime, datetime]],
        target_date: date,
    ) -> list[tuple[datetime, datetime]]:
        """Remove slots that overlap with confirmed bookings."""
        if not candidates:
            return candidates

        day_start = self.tz.localize(datetime.combine(target_date, time.min))
        day_end = self.tz.localize(datetime.combine(target_date, time.max))

        bookings = Booking.objects.filter(
            calendar=self.calendar,
            start_time__lt=day_end,
            end_time__gt=day_start,
            status__in=["confirmed", "pending"],
        )

        if not bookings.exists():
            return candidates

        buffer_before = self.calendar.buffer_before
        buffer_after = self.calendar.buffer_after

        filtered = []
        for slot_start, slot_end in candidates:
            # Include buffer in overlap check
            check_start = slot_start - timedelta(minutes=buffer_before)
            check_end = slot_end + timedelta(minutes=buffer_after)

            is_booked = False
            for booking in bookings:
                if check_start < booking.end_time and check_end > booking.start_time:
                    is_booked = True
                    break
            if not is_booked:
                filtered.append((slot_start, slot_end))

        return filtered

    def _filter_minimum_notice(
        self,
        candidates: list[tuple[datetime, datetime]],
        now: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Remove slots that are within the minimum notice period."""
        if not candidates or self.calendar.minimum_notice == 0:
            return candidates

        notice_cutoff = now + timedelta(hours=self.calendar.minimum_notice)
        return [
            (start, end)
            for start, end in candidates
            if start >= notice_cutoff
        ]

    def _filter_max_daily_bookings(
        self,
        candidates: list[tuple[datetime, datetime]],
        target_date: date,
    ) -> list[tuple[datetime, datetime]]:
        """Remove all slots if maximum daily bookings has been reached."""
        max_bookings = self.calendar.max_bookings_per_day
        if not candidates or max_bookings == 0:
            return candidates

        day_start = self.tz.localize(datetime.combine(target_date, time.min))
        day_end = self.tz.localize(datetime.combine(target_date, time.max))

        current_count = Booking.objects.filter(
            calendar=self.calendar,
            start_time__gte=day_start,
            start_time__lt=day_end,
            status__in=["confirmed", "pending"],
        ).count()

        if current_count >= max_bookings:
            return []

        return candidates

    def get_available_dates(
        self,
        start_date: date,
        end_date: date,
        duration_minutes: int = 30,
    ) -> list[date]:
        """
        Get all dates with at least one available slot within a date range.
        Useful for calendar date pickers on booking pages.
        """
        available_dates = []
        current = start_date

        while current <= end_date:
            slots = self.get_available_slots(current, duration_minutes)
            if slots:
                available_dates.append(current)
            current += timedelta(days=1)

        return available_dates


def check_slot_availability(
    calendar: Calendar,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[str] = None,
) -> bool:
    """
    Quick check if a specific time slot is available.
    Used for booking creation and rescheduling validation.
    """
    bookings_query = Booking.objects.filter(
        calendar=calendar,
        start_time__lt=end_time,
        end_time__gt=start_time,
        status__in=["confirmed", "pending"],
    )

    if exclude_booking_id:
        bookings_query = bookings_query.exclude(id=exclude_booking_id)

    if bookings_query.exists():
        return False

    # Check blocked times
    blocked = BlockedTime.objects.filter(
        calendar=calendar,
        start_datetime__lt=end_time,
        end_datetime__gt=start_time,
    )

    return not blocked.exists()
