/**
 * Dashboard page for authenticated providers.
 * Shows stats overview, upcoming bookings, and quick actions.
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon } from '@heroicons/react/24/outline';
import ProviderDashboard from '../components/providers/ProviderDashboard';
import { useBookings } from '../hooks/useBookings';
import { useAppSelector } from '../store';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const {
    bookings,
    stats,
    isLoading,
    loadStats,
    confirm,
    updateFilters,
  } = useBookings(false);

  useEffect(() => {
    loadStats();
    updateFilters({ time_filter: 'upcoming', page_size: 10 });
  }, [loadStats, updateFilters]);

  const handleViewBooking = (id: string) => {
    navigate(`/bookings/${id}`);
  };

  const handleConfirmBooking = async (id: string) => {
    await confirm(id);
    loadStats();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.first_name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here's what's happening with your bookings today.
          </p>
        </div>
        <button
          onClick={() => navigate('/services/new')}
          className="inline-flex items-center px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Event Type
        </button>
      </div>

      {/* Dashboard content */}
      <ProviderDashboard
        stats={stats}
        upcomingBookings={bookings}
        userTimezone={user?.timezone || 'America/New_York'}
        onViewBooking={handleViewBooking}
        onConfirmBooking={handleConfirmBooking}
      />
    </div>
  );
}
