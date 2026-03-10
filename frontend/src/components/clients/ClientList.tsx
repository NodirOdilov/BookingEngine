/**
 * Client list component.
 * Displays a table of clients derived from booking invitees.
 */

import React, { useMemo, useState } from 'react';
import {
  MagnifyingGlassIcon,
  EnvelopeIcon,
  PhoneIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { Booking } from '../../api/bookings';
import { formatDateTime } from '../../utils/dateUtils';

interface Client {
  email: string;
  name: string;
  phone: string;
  bookingCount: number;
  lastBookingDate: string;
  status: string;
}

interface ClientListProps {
  bookings: Booking[];
  userTimezone: string;
  onViewClient: (email: string) => void;
}

export default function ClientList({
  bookings,
  userTimezone,
  onViewClient,
}: ClientListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Derive unique clients from bookings
  const clients = useMemo(() => {
    const clientMap = new Map<string, Client>();

    bookings.forEach((booking) => {
      const existing = clientMap.get(booking.invitee_email);
      if (existing) {
        existing.bookingCount += 1;
        if (booking.start_time > existing.lastBookingDate) {
          existing.lastBookingDate = booking.start_time;
        }
      } else {
        clientMap.set(booking.invitee_email, {
          email: booking.invitee_email,
          name: booking.invitee_name,
          phone: booking.invitee_phone || '',
          bookingCount: 1,
          lastBookingDate: booking.start_time,
          status: booking.status,
        });
      }
    });

    return Array.from(clientMap.values()).sort(
      (a, b) => b.lastBookingDate.localeCompare(a.lastBookingDate)
    );
  }, [bookings]);

  const filtered = useMemo(() => {
    if (!searchQuery) return clients;
    const q = searchQuery.toLowerCase();
    return clients.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.phone.includes(q)
    );
  }, [clients, searchQuery]);

  return (
    <div>
      {/* Search bar */}
      <div className="mb-5">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search clients by name, email, or phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Client table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Client
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bookings
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Booking
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-sm text-gray-500">
                  {searchQuery
                    ? 'No clients match your search.'
                    : 'No clients yet. Clients appear here after their first booking.'}
                </td>
              </tr>
            ) : (
              filtered.map((client) => (
                <tr
                  key={client.email}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onViewClient(client.email)}
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {client.name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')
                            .slice(0, 2)
                            .toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {client.name}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="space-y-0.5">
                      <div className="flex items-center text-sm text-gray-500">
                        <EnvelopeIcon className="w-3.5 h-3.5 mr-1.5" />
                        {client.email}
                      </div>
                      {client.phone && (
                        <div className="flex items-center text-sm text-gray-500">
                          <PhoneIcon className="w-3.5 h-3.5 mr-1.5" />
                          {client.phone}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center text-sm text-gray-900">
                      <CalendarIcon className="w-4 h-4 mr-1.5 text-gray-400" />
                      {client.bookingCount}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-500">
                    {formatDateTime(
                      client.lastBookingDate,
                      userTimezone,
                      'MMM d, yyyy'
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
