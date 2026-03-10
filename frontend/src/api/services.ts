/**
 * Event Types (Services) API module.
 * Handles CRUD for event types, locations, settings, and public endpoints.
 */

import apiClient from './client';

export interface EventType {
  id: string;
  name: string;
  slug: string;
  description: string;
  instructions: string;
  color: string;
  duration: number;
  scheduling_type: 'one_on_one' | 'round_robin' | 'collective' | 'group';
  max_participants: number;
  is_paid: boolean;
  price: string;
  currency: string;
  buffer_before: number | null;
  buffer_after: number | null;
  minimum_notice: number | null;
  max_bookings_per_day: number | null;
  custom_questions: CustomQuestion[];
  requires_confirmation: boolean;
  is_active: boolean;
  is_secret: boolean;
  locations: EventLocation[];
  booking_url: string;
  calendar: string;
  created_at: string;
}

export interface CustomQuestion {
  label: string;
  type: 'text' | 'textarea' | 'select' | 'checkbox';
  required: boolean;
  options?: string[];
}

export interface EventLocation {
  id: string;
  location_type: string;
  location_type_display: string;
  address: string;
  phone_number: string;
  additional_info: string;
  position: number;
  is_default: boolean;
}

export interface EventTypeSettings {
  id: string;
  email_reminder_enabled: boolean;
  email_reminder_minutes: number[];
  sms_reminder_enabled: boolean;
  sms_reminder_minutes: number[];
  follow_up_enabled: boolean;
  follow_up_delay_hours: number;
  max_events_per_day: number;
  rolling_days_window: number;
  slot_interval: number;
  show_remaining_slots: boolean;
  allow_cancellation: boolean;
  allow_rescheduling: boolean;
  cancellation_notice_hours: number;
}

export const eventTypesApi = {
  list: () =>
    apiClient.get<EventType[]>('/event-types/'),

  get: (id: string) =>
    apiClient.get<EventType>(`/event-types/${id}/`),

  create: (data: Partial<EventType>) =>
    apiClient.post<EventType>('/event-types/', data),

  update: (id: string, data: Partial<EventType>) =>
    apiClient.patch<EventType>(`/event-types/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/event-types/${id}/`),

  duplicate: (id: string) =>
    apiClient.post<EventType>(`/event-types/${id}/duplicate/`),

  toggleActive: (id: string) =>
    apiClient.post<{ is_active: boolean }>(`/event-types/${id}/toggle-active/`),

  // Settings
  getSettings: (id: string) =>
    apiClient.get<EventTypeSettings>(`/event-types/${id}/settings/`),

  updateSettings: (id: string, data: Partial<EventTypeSettings>) =>
    apiClient.patch<EventTypeSettings>(`/event-types/${id}/settings/`, data),

  // Locations
  getLocations: (id: string) =>
    apiClient.get<EventLocation[]>(`/event-types/${id}/locations/`),

  addLocation: (id: string, data: Partial<EventLocation>) =>
    apiClient.post<EventLocation>(`/event-types/${id}/locations/`, data),
};

// Public endpoints
export const publicEventTypesApi = {
  listByUser: (userSlug: string) =>
    apiClient.get<EventType[]>(`/event-types/public/${userSlug}/`),

  getBySlug: (userSlug: string, eventSlug: string) =>
    apiClient.get<EventType>(`/event-types/public/${userSlug}/${eventSlug}/`),
};
