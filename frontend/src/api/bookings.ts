/**
 * Bookings API module.
 * Handles all booking-related API calls for both authenticated and public endpoints.
 */

import apiClient from './client';

export interface Booking {
  id: string;
  reference: string;
  event_type: string;
  event_type_name?: string;
  calendar: string;
  host: { id: string; email: string; full_name: string };
  invitee_name: string;
  invitee_email: string;
  invitee_phone: string;
  invitee_timezone: string;
  invitee_notes: string;
  custom_responses: Record<string, string>;
  start_time: string;
  end_time: string;
  duration: number;
  status: BookingStatus;
  location_type: string;
  location_detail: string;
  meeting_link: string;
  is_paid: boolean;
  payment_amount: string;
  payment_status: string;
  is_upcoming: boolean;
  is_past: boolean;
  can_cancel: boolean;
  can_reschedule: boolean;
  created_at: string;
}

export type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'cancelled'
  | 'completed'
  | 'no_show'
  | 'rescheduled';

export interface BookingListParams {
  status?: BookingStatus;
  time_filter?: 'upcoming' | 'past';
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface CreateBookingPayload {
  event_type: string;
  start_time: string;
  invitee_name: string;
  invitee_email: string;
  invitee_phone?: string;
  invitee_timezone: string;
  invitee_notes?: string;
  custom_responses?: Record<string, string>;
  location_type?: string;
  location_detail?: string;
  source?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface BookingStats {
  upcoming_count: number;
  today_count: number;
  pending_count: number;
  week_count: number;
  month_count: number;
  cancellation_rate: number;
  no_show_rate: number;
}

// Authenticated endpoints
export const bookingsApi = {
  list: (params?: BookingListParams) =>
    apiClient.get<PaginatedResponse<Booking>>('/bookings/', { params }),

  get: (id: string) =>
    apiClient.get<Booking>(`/bookings/${id}/`),

  confirm: (id: string) =>
    apiClient.post<Booking>(`/bookings/${id}/confirm/`),

  cancel: (id: string, reason: string, notes = '') =>
    apiClient.post<Booking>(`/bookings/${id}/cancel/`, { reason, notes }),

  reschedule: (id: string, newStartTime: string, reason = '') =>
    apiClient.post<Booking>(`/bookings/${id}/reschedule/`, {
      new_start_time: newStartTime,
      reason,
    }),

  markCompleted: (id: string) =>
    apiClient.post<Booking>(`/bookings/${id}/mark-completed/`),

  markNoShow: (id: string) =>
    apiClient.post<Booking>(`/bookings/${id}/mark-no-show/`),

  addNote: (id: string, content: string, isInternal = true) =>
    apiClient.post(`/bookings/${id}/notes/`, { content, is_internal: isInternal }),

  getNotes: (id: string) =>
    apiClient.get(`/bookings/${id}/notes/`),

  getStats: () =>
    apiClient.get<BookingStats>('/bookings/stats/'),
};

// Public endpoints (no auth required)
export const publicBookingsApi = {
  create: (data: CreateBookingPayload) =>
    apiClient.post<Booking>('/bookings/public/create/', data),

  getByReference: (reference: string) =>
    apiClient.get<Booking>(`/bookings/public/${reference}/`),

  cancel: (reference: string, reason: string, notes = '') =>
    apiClient.put(`/bookings/public/${reference}/cancel/`, { reason, notes }),

  reschedule: (reference: string, newStartTime: string, reason = '') =>
    apiClient.put(`/bookings/public/${reference}/reschedule/`, {
      new_start_time: newStartTime,
      reason,
    }),
};
