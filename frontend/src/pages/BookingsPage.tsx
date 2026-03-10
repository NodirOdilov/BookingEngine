/**
 * Bookings page for managing all appointments.
 * Lists bookings with filters, search, and status management actions.
 */

import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircleIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { useBookings } from '../hooks/useBookings';
import { useAppSelector } from '../store';
import StatusBadge from '../components/common/StatusBadge';
import { formatDateTime, formatDuration } from '../utils/dateUtils';
import { BookingStatus } from '../api/bookings';
import toast from 'react-hot-toast';

const STATUS_TABS: Array<{ label: string; value: BookingStatus | undefined }> = [
  { label: 'All', value: undefined },
  { label: 'Upcoming', value: undefined },
  { label: 'Pending', value: 'pending' },
  { label: 'Confirmed', value: 'confirmed' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
];

export default function BookingsPage() {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const {
    bookings,
    totalCount,
    currentPage,
    totalPages,
    isLoading,
    filters,
    confirm,
    cancel,
    updateFilters,
    goToPage,
    filterByStatus,
  } = useBookings();

  const tz = user?.timezone || 'America/New_York';

  const handleConfirm = useCallback(
    async (id: string) => {
      await confirm(id);
      toast.success('Booking confirmed');
    },
    [confirm]
  );

  const handleCancel = useCallback(
    async (id: string) => {
      await cancel(id, 'host_cancelled');
      toast.success('Booking cancelled');
    },
    [cancel]
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
        <span className="text-sm text-gray-500">{totalCount} total</span>
      </div>

      {/* Filters bar */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, email, or reference..."
            onChange={(e) => updateFilters({ search: e.target.value })}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Status tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.label}
              onClick={() => {
                if (tab.label === 'Upcoming') {
                  updateFilters({ status: undefined, time_filter: 'upcoming' });
                } else {
                  updateFilters({ status: tab.value, time_filter: undefined });
                }
              }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                filters.status === tab.value &&
                (tab.label !== 'Upcoming' || filters.time_filter === 'upcoming')
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Bookings table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : bookings.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-sm text-gray-500">No bookings found.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Invitee
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Event
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date & Time
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {bookings.map((booking) => (
                <tr
                  key={booking.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/bookings/${booking.id}`)}
                >
                  <td className="px-5 py-4">
                    <p className="text-sm font-medium text-gray-900">
                      {booking.invitee_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {booking.invitee_email}
                    </p>
                  </td>
                  <td className="px-5 py-4">
                    <p className="text-sm text-gray-700">
                      {booking.event_type_name || 'Meeting'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDuration(booking.duration)}
                    </p>
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-700">
                    {formatDateTime(booking.start_time, tz, 'MMM d, yyyy h:mm a')}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={booking.status} />
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div
                      className="flex items-center justify-end space-x-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {booking.status === 'pending' && (
                        <button
                          onClick={() => handleConfirm(booking.id)}
                          className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                          title="Confirm"
                        >
                          <CheckCircleIcon className="w-4 h-4" />
                        </button>
                      )}
                      {(booking.status === 'pending' ||
                        booking.status === 'confirmed') && (
                        <button
                          onClick={() => handleCancel(booking.id)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                          title="Cancel"
                        >
                          <XCircleIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Page {currentPage} of {totalPages}
            </p>
            <div className="flex space-x-2">
              <button
                disabled={currentPage <= 1}
                onClick={() => goToPage(currentPage - 1)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => goToPage(currentPage + 1)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
