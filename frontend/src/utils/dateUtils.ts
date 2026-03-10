/**
 * Date utility functions for BookingEngine frontend.
 * Handles timezone conversions, formatting, and calendar computations.
 */

import {
  format,
  parseISO,
  isToday,
  isTomorrow,
  isPast,
  isFuture,
  differenceInMinutes,
  differenceInHours,
  differenceInDays,
  addDays,
  addMinutes,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  getDay,
} from 'date-fns';
import { formatInTimeZone, toZonedTime } from 'date-fns-tz';

/**
 * Format a datetime string in the user's timezone.
 */
export function formatDateTime(
  dateStr: string,
  tz: string = 'America/New_York',
  formatStr: string = 'MMM d, yyyy h:mm a'
): string {
  return formatInTimeZone(parseISO(dateStr), tz, formatStr);
}

/**
 * Format just the time portion of a datetime.
 */
export function formatTime(
  dateStr: string,
  tz: string = 'America/New_York',
  use24h: boolean = false
): string {
  const formatStr = use24h ? 'HH:mm' : 'h:mm a';
  return formatInTimeZone(parseISO(dateStr), tz, formatStr);
}

/**
 * Format a date for display (e.g., "Today", "Tomorrow", "Wed, Jan 15").
 */
export function formatDateRelative(dateStr: string): string {
  const date = parseISO(dateStr);
  if (isToday(date)) return 'Today';
  if (isTomorrow(date)) return 'Tomorrow';
  return format(date, 'EEE, MMM d');
}

/**
 * Format a duration in minutes to a human-readable string.
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  if (remaining === 0) return `${hours} hr`;
  return `${hours} hr ${remaining} min`;
}

/**
 * Get a relative time description (e.g., "in 2 hours", "3 days ago").
 */
export function getRelativeTime(dateStr: string): string {
  const date = parseISO(dateStr);
  const now = new Date();

  if (isFuture(date)) {
    const mins = differenceInMinutes(date, now);
    if (mins < 60) return `in ${mins} min`;
    const hours = differenceInHours(date, now);
    if (hours < 24) return `in ${hours} hr`;
    const days = differenceInDays(date, now);
    return `in ${days} day${days > 1 ? 's' : ''}`;
  }

  const mins = differenceInMinutes(now, date);
  if (mins < 60) return `${mins} min ago`;
  const hours = differenceInHours(now, date);
  if (hours < 24) return `${hours} hr ago`;
  const days = differenceInDays(now, date);
  return `${days} day${days > 1 ? 's' : ''} ago`;
}

/**
 * Generate an array of dates for a month grid (6 weeks).
 */
export function getMonthGrid(year: number, month: number): Date[] {
  const monthStart = startOfMonth(new Date(year, month));
  const monthEnd = endOfMonth(monthStart);
  const gridStart = startOfWeek(monthStart, { weekStartsOn: 0 });
  const gridEnd = endOfWeek(monthEnd, { weekStartsOn: 0 });

  return eachDayOfInterval({ start: gridStart, end: gridEnd });
}

/**
 * Generate week dates starting from a given date.
 */
export function getWeekDates(referenceDate: Date): Date[] {
  const weekStart = startOfWeek(referenceDate, { weekStartsOn: 0 });
  return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
}

/**
 * Generate time slot options for a duration picker.
 */
export function getTimeSlotOptions(
  startHour: number = 0,
  endHour: number = 24,
  intervalMinutes: number = 30
): Array<{ label: string; value: string }> {
  const slots: Array<{ label: string; value: string }> = [];
  const base = new Date(2000, 0, 1, startHour, 0);
  const end = new Date(2000, 0, 1, endHour, 0);

  let current = base;
  while (current < end) {
    slots.push({
      label: format(current, 'h:mm a'),
      value: format(current, 'HH:mm'),
    });
    current = addMinutes(current, intervalMinutes);
  }

  return slots;
}

/**
 * Get day name from day index (0 = Monday in our backend).
 */
export function getDayName(dayIndex: number): string {
  const days = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];
  return days[dayIndex] || '';
}

/**
 * Check if a date string falls on a specific day of the week.
 */
export function isDayOfWeek(dateStr: string, dayIndex: number): boolean {
  const date = parseISO(dateStr);
  const jsDay = getDay(date); // 0=Sun, 1=Mon, ...
  // Our backend uses 0=Mon, so convert
  const backendDay = jsDay === 0 ? 6 : jsDay - 1;
  return backendDay === dayIndex;
}

/**
 * Convert a timezone-aware datetime to a different timezone for display.
 */
export function convertTimezone(
  dateStr: string,
  fromTz: string,
  toTz: string
): Date {
  const date = parseISO(dateStr);
  return toZonedTime(date, toTz);
}
