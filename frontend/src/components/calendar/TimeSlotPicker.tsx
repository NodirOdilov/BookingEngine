/**
 * Time slot picker component for the public booking flow.
 * Displays available time slots for a selected date and allows selection.
 */

import React from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';
import { TimeSlot } from '../../api/calendars';
import { formatTime } from '../../utils/dateUtils';

interface TimeSlotPickerProps {
  slots: TimeSlot[];
  selectedSlot: TimeSlot | null;
  onSlotSelect: (slot: TimeSlot) => void;
  timezone: string;
  isLoading: boolean;
  dateLabel: string;
}

export default function TimeSlotPicker({
  slots,
  selectedSlot,
  onSlotSelect,
  timezone,
  isLoading,
  dateLabel,
}: TimeSlotPickerProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <p className="mt-3 text-sm text-gray-500">Loading available times...</p>
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="text-center py-8">
        <ClockIcon className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-3 text-sm font-medium text-gray-900">
          No available times
        </p>
        <p className="mt-1 text-sm text-gray-500">
          Try selecting a different date.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-900 mb-3">{dateLabel}</h3>
      <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
        {slots.map((slot, idx) => {
          const isSelected =
            selectedSlot && selectedSlot.start_utc === slot.start_utc;

          return (
            <button
              key={idx}
              onClick={() => onSlotSelect(slot)}
              className={`
                w-full px-4 py-3 rounded-lg border text-sm font-medium
                transition-all focus:outline-none focus:ring-2 focus:ring-blue-500
                ${
                  isSelected
                    ? 'border-blue-600 bg-blue-600 text-white shadow-sm'
                    : 'border-gray-200 text-gray-700 hover:border-blue-300 hover:bg-blue-50'
                }
              `}
            >
              <div className="flex items-center justify-between">
                <span>{formatTime(slot.start, timezone)}</span>
                {isSelected && (
                  <span className="text-xs bg-white/20 px-2 py-0.5 rounded">
                    Confirm
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
