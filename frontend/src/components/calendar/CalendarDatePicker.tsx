/**
 * Calendar date picker component for the public booking flow.
 * Highlights available dates and allows date selection.
 */

import React, { useMemo, useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import {
  format,
  addMonths,
  subMonths,
  isSameDay,
  isSameMonth,
  isToday,
  isBefore,
  startOfDay,
} from 'date-fns';
import { getMonthGrid } from '../../utils/dateUtils';

interface CalendarDatePickerProps {
  selectedDate: Date | null;
  availableDates: string[];
  onDateSelect: (date: Date) => void;
  minDate?: Date;
  maxDate?: Date;
}

export default function CalendarDatePicker({
  selectedDate,
  availableDates,
  onDateSelect,
  minDate = new Date(),
}: CalendarDatePickerProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const monthGrid = useMemo(
    () => getMonthGrid(currentMonth.getFullYear(), currentMonth.getMonth()),
    [currentMonth]
  );

  const availableSet = useMemo(
    () => new Set(availableDates),
    [availableDates]
  );

  const isDateAvailable = (date: Date): boolean => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return availableSet.has(dateStr);
  };

  const isDateDisabled = (date: Date): boolean => {
    if (isBefore(startOfDay(date), startOfDay(minDate))) return true;
    if (!isSameMonth(date, currentMonth)) return true;
    return !isDateAvailable(date);
  };

  return (
    <div className="w-full max-w-sm">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
          className="p-1.5 rounded-md hover:bg-gray-100"
          aria-label="Previous month"
        >
          <ChevronLeftIcon className="w-5 h-5 text-gray-600" />
        </button>
        <h3 className="text-sm font-semibold text-gray-900">
          {format(currentMonth, 'MMMM yyyy')}
        </h3>
        <button
          onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
          className="p-1.5 rounded-md hover:bg-gray-100"
          aria-label="Next month"
        >
          <ChevronRightIcon className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 mb-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="text-center text-xs font-medium text-gray-500 py-1"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Date grid */}
      <div className="grid grid-cols-7 gap-1">
        {monthGrid.map((date, idx) => {
          const disabled = isDateDisabled(date);
          const selected = selectedDate && isSameDay(date, selectedDate);
          const today = isToday(date);
          const inCurrentMonth = isSameMonth(date, currentMonth);

          return (
            <button
              key={idx}
              disabled={disabled}
              onClick={() => !disabled && onDateSelect(date)}
              className={`
                relative h-10 w-full rounded-lg text-sm font-medium
                transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
                ${!inCurrentMonth ? 'text-gray-300' : ''}
                ${disabled && inCurrentMonth ? 'text-gray-300 cursor-not-allowed' : ''}
                ${
                  selected
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : !disabled
                    ? 'text-gray-900 hover:bg-blue-50'
                    : ''
                }
              `}
            >
              {format(date, 'd')}
              {today && !selected && (
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-blue-600" />
              )}
              {!disabled && !selected && isDateAvailable(date) && (
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-green-500" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
