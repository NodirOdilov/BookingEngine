/**
 * Calendars API module.
 * Handles calendar CRUD, availability rules, blocked times, and available slots.
 */

import apiClient from './client';

export interface Calendar {
  id: string;
  name: string;
  description: string;
  timezone: string;
  is_default: boolean;
  is_active: boolean;
  color: string;
  buffer_before: number;
  buffer_after: number;
  minimum_notice: number;
  max_days_ahead: number;
  max_bookings_per_day: number;
  availability_rules_count: number;
  created_at: string;
}

export interface AvailabilityRule {
  id: string;
  calendar: string;
  rule_type: 'weekly' | 'date_override';
  day_of_week: number | null;
  day_name: string | null;
  specific_date: string | null;
  start_time: string;
  end_time: string;
  is_available: boolean;
}

export interface BlockedTime {
  id: string;
  calendar: string;
  title: string;
  reason: string;
  start_datetime: string;
  end_datetime: string;
  is_all_day: boolean;
}

export interface TimeSlot {
  start: string;
  end: string;
  start_utc: string;
  end_utc: string;
}

export interface AvailableSlotsResponse {
  date: string;
  timezone: string;
  duration_minutes: number;
  slots: TimeSlot[];
  count: number;
}

export interface AvailableDatesResponse {
  start_date: string;
  end_date: string;
  available_dates: string[];
  count: number;
}

export const calendarsApi = {
  list: () =>
    apiClient.get<Calendar[]>('/calendars/'),

  get: (id: string) =>
    apiClient.get<Calendar>(`/calendars/${id}/`),

  create: (data: Partial<Calendar>) =>
    apiClient.post<Calendar>('/calendars/', data),

  update: (id: string, data: Partial<Calendar>) =>
    apiClient.patch<Calendar>(`/calendars/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/calendars/${id}/`),

  // Availability rules
  getAvailabilityRules: (calendarId: string) =>
    apiClient.get<AvailabilityRule[]>(
      `/calendars/${calendarId}/availability-rules/`
    ),

  createAvailabilityRule: (calendarId: string, data: Partial<AvailabilityRule>) =>
    apiClient.post<AvailabilityRule>(
      `/calendars/${calendarId}/availability-rules/`,
      data
    ),

  setBulkAvailability: (calendarId: string, rules: Partial<AvailabilityRule>[]) =>
    apiClient.post(
      `/calendars/${calendarId}/bulk-availability/`,
      { rules }
    ),

  deleteAvailabilityRule: (ruleId: string) =>
    apiClient.delete(`/calendars/availability-rules/${ruleId}/`),

  // Blocked times
  getBlockedTimes: (calendarId: string) =>
    apiClient.get<BlockedTime[]>(`/calendars/${calendarId}/blocked-times/`),

  createBlockedTime: (calendarId: string, data: Partial<BlockedTime>) =>
    apiClient.post<BlockedTime>(
      `/calendars/${calendarId}/blocked-times/`,
      data
    ),

  deleteBlockedTime: (blockedTimeId: string) =>
    apiClient.delete(`/calendars/blocked-times/${blockedTimeId}/`),

  // Available slots (public-facing)
  getAvailableSlots: (
    calendarId: string,
    date: string,
    timezone: string,
    duration?: number
  ) =>
    apiClient.get<AvailableSlotsResponse>(
      `/calendars/${calendarId}/available-slots/`,
      { params: { date, timezone, duration } }
    ),

  getAvailableDates: (
    calendarId: string,
    startDate: string,
    endDate: string,
    duration?: number
  ) =>
    apiClient.get<AvailableDatesResponse>(
      `/calendars/${calendarId}/available-dates/`,
      { params: { start_date: startDate, end_date: endDate, duration } }
    ),
};
