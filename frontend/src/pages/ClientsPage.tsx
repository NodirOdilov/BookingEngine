/**
 * Clients page.
 * Displays a list of clients derived from booking data.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserGroupIcon } from '@heroicons/react/24/outline';
import ClientList from '../components/clients/ClientList';
import { Booking, bookingsApi } from '../api/bookings';
import { useAppSelector } from '../store';

export default function ClientsPage() {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAllBookings = useCallback(async () => {
    try {
      setIsLoading(true);
      // Fetch all bookings to derive client list
      const { data } = await bookingsApi.list({ page_size: 500 });
      setBookings(data.results);
    } catch {
      // handled silently
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllBookings();
  }, [fetchAllBookings]);

  const handleViewClient = (email: string) => {
    navigate(`/bookings?search=${encodeURIComponent(email)}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
          <p className="mt-1 text-sm text-gray-500">
            View and manage your booking clients.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : bookings.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <UserGroupIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900">
            No clients yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Clients will appear here after their first booking.
          </p>
        </div>
      ) : (
        <ClientList
          bookings={bookings}
          userTimezone={user?.timezone || 'America/New_York'}
          onViewClient={handleViewClient}
        />
      )}
    </div>
  );
}
