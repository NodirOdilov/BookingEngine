/**
 * Application constants for BookingEngine frontend.
 */

export const BOOKING_STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
  completed: 'Completed',
  no_show: 'No Show',
  rescheduled: 'Rescheduled',
};

export const BOOKING_STATUS_COLORS: Record<
  string,
  { bg: string; text: string; dot: string }
> = {
  pending: { bg: 'bg-amber-100', text: 'text-amber-800', dot: 'bg-amber-400' },
  confirmed: { bg: 'bg-green-100', text: 'text-green-800', dot: 'bg-green-400' },
  cancelled: { bg: 'bg-red-100', text: 'text-red-800', dot: 'bg-red-400' },
  completed: { bg: 'bg-blue-100', text: 'text-blue-800', dot: 'bg-blue-400' },
  no_show: { bg: 'bg-gray-100', text: 'text-gray-800', dot: 'bg-gray-400' },
  rescheduled: {
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    dot: 'bg-purple-400',
  },
};

export const EVENT_COLORS = [
  { value: '#3B82F6', label: 'Blue' },
  { value: '#10B981', label: 'Green' },
  { value: '#F59E0B', label: 'Amber' },
  { value: '#EF4444', label: 'Red' },
  { value: '#8B5CF6', label: 'Purple' },
  { value: '#EC4899', label: 'Pink' },
  { value: '#06B6D4', label: 'Cyan' },
  { value: '#F97316', label: 'Orange' },
];

export const DURATION_OPTIONS = [
  { value: 15, label: '15 minutes' },
  { value: 30, label: '30 minutes' },
  { value: 45, label: '45 minutes' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
];

export const LOCATION_TYPES = [
  { value: 'in_person', label: 'In Person', icon: 'MapPinIcon' },
  { value: 'phone_incoming', label: 'Phone (invitee calls)', icon: 'PhoneIcon' },
  { value: 'phone_outgoing', label: 'Phone (I will call)', icon: 'PhoneArrowUpRightIcon' },
  { value: 'google_meet', label: 'Google Meet', icon: 'VideoCameraIcon' },
  { value: 'zoom', label: 'Zoom', icon: 'VideoCameraIcon' },
  { value: 'microsoft_teams', label: 'Microsoft Teams', icon: 'VideoCameraIcon' },
  { value: 'custom_link', label: 'Custom Link', icon: 'LinkIcon' },
  { value: 'ask_invitee', label: 'Ask Invitee', icon: 'ChatBubbleLeftIcon' },
];

export const TIMEZONE_OPTIONS = [
  { group: 'US & Canada', zones: [
    { value: 'America/New_York', label: 'Eastern Time (ET)' },
    { value: 'America/Chicago', label: 'Central Time (CT)' },
    { value: 'America/Denver', label: 'Mountain Time (MT)' },
    { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
    { value: 'America/Anchorage', label: 'Alaska (AKT)' },
    { value: 'Pacific/Honolulu', label: 'Hawaii (HST)' },
  ]},
  { group: 'Europe', zones: [
    { value: 'Europe/London', label: 'London (GMT/BST)' },
    { value: 'Europe/Paris', label: 'Paris (CET)' },
    { value: 'Europe/Berlin', label: 'Berlin (CET)' },
    { value: 'Europe/Moscow', label: 'Moscow (MSK)' },
  ]},
  { group: 'Asia', zones: [
    { value: 'Asia/Dubai', label: 'Dubai (GST)' },
    { value: 'Asia/Kolkata', label: 'India (IST)' },
    { value: 'Asia/Shanghai', label: 'China (CST)' },
    { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  ]},
  { group: 'Pacific', zones: [
    { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
    { value: 'Pacific/Auckland', label: 'Auckland (NZST)' },
  ]},
];

export const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  CALENDAR: '/calendar',
  BOOKINGS: '/bookings',
  SERVICES: '/services',
  CLIENTS: '/clients',
  SETTINGS: '/settings',
  PUBLIC_BOOKING: '/p/:userSlug',
  PUBLIC_EVENT_TYPE: '/p/:userSlug/:eventSlug',
} as const;
