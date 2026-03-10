/**
 * Provider dashboard component.
 * Shows upcoming bookings, quick stats, and action shortcuts for the host.
 */

import React from 'react';
import {
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import { BookingStats } from '../../api/bookings';
import { Booking } from '../../api/bookings';
import { formatDateTime, formatDuration, getRelativeTime } from '../../utils/dateUtils';
import { BOOKING_STATUS_COLORS, BOOKING_STATUS_LABELS } from '../../utils/constants';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
  subtext?: string;
}

function StatCard({ label, value, icon: Icon, color, subtext }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
          {subtext && (
            <p className="mt-0.5 text-xs text-gray-400">{subtext}</p>
          )}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

interface ProviderDashboardProps {
  stats: BookingStats | null;
  upcomingBookings: Booking[];
  userTimezone: string;
  onViewBooking: (id: string) => void;
  onConfirmBooking: (id: string) => void;
}

export default function ProviderDashboard({
  stats,
  upcomingBookings,
  userTimezone,
  onViewBooking,
  onConfirmBooking,
}: ProviderDashboardProps) {
  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Today's Bookings"
          value={stats?.today_count ?? 0}
          icon={CalendarIcon}
          color="bg-blue-500"
        />
        <StatCard
          label="Upcoming"
          value={stats?.upcoming_count ?? 0}
          icon={ClockIcon}
          color="bg-green-500"
        />
        <StatCard
          label="Pending Approval"
          value={stats?.pending_count ?? 0}
          icon={ExclamationCircleIcon}
          color="bg-amber-500"
        />
        <StatCard
          label="This Month"
          value={stats?.month_count ?? 0}
          icon={UserGroupIcon}
          color="bg-purple-500"
          subtext={`${stats?.cancellation_rate ?? 0}% cancellation rate`}
        />
      </div>

      {/* Upcoming bookings list */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">
            Upcoming Bookings
          </h2>
        </div>
        <div className="divide-y divide-gray-100">
          {upcomingBookings.length === 0 ? (
            <div className="p-8 text-center">
              <CalendarIcon className="mx-auto h-10 w-10 text-gray-300" />
              <p className="mt-2 text-sm text-gray-500">
                No upcoming bookings
              </p>
            </div>
          ) : (
            upcomingBookings.map((booking) => {
              const statusStyle =
                BOOKING_STATUS_COLORS[booking.status] ||
                BOOKING_STATUS_COLORS.confirmed;

              return (
                <div
                  key={booking.id}
                  className="px-5 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => onViewBooking(booking.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {booking.invitee_name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')
                            .slice(0, 2)}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {booking.invitee_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {booking.event_type_name ||
                            `${formatDuration(booking.duration)} meeting`}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-900">
                        {formatDateTime(
                          booking.start_time,
                          userTimezone,
                          'MMM d, h:mm a'
                        )}
                      </p>
                      <div className="flex items-center justify-end mt-1 space-x-2">
                        <span
                          className={`inline-flex items-center text-xs px-2 py-0.5 rounded-full ${statusStyle.bg} ${statusStyle.text}`}
                        >
                          {BOOKING_STATUS_LABELS[booking.status]}
                        </span>
                        {booking.status === 'pending' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onConfirmBooking(booking.id);
                            }}
                            className="text-xs text-green-600 hover:text-green-800 font-medium"
                          >
                            Confirm
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
