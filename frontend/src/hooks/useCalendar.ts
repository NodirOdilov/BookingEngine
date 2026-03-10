/**
 * Custom hook for calendar and availability operations.
 * Manages calendar selection, date picking, and slot fetching.
 */

import { useCallback, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
  fetchAvailableDates,
  fetchAvailableSlots,
  fetchAvailabilityRules,
  fetchCalendars,
  selectCalendar,
  selectDate,
} from '../store/calendarSlice';
import { Calendar } from '../api/calendars';
import { format, addDays } from 'date-fns';

export function useCalendar() {
  const dispatch = useAppDispatch();
  const {
    calendars,
    selectedCalendar,
    availabilityRules,
    availableSlots,
    availableDates,
    selectedDate,
    isLoading,
    isSlotsLoading,
  } = useAppSelector((state) => state.calendar);

  useEffect(() => {
    dispatch(fetchCalendars());
  }, [dispatch]);

  const setSelectedCalendar = useCallback(
    (calendar: Calendar) => {
      dispatch(selectCalendar(calendar));
    },
    [dispatch]
  );

  const loadRules = useCallback(
    (calendarId: string) => {
      dispatch(fetchAvailabilityRules(calendarId));
    },
    [dispatch]
  );

  const setSelectedDate = useCallback(
    (date: string | null) => {
      dispatch(selectDate(date));
    },
    [dispatch]
  );

  const loadSlots = useCallback(
    (calendarId: string, date: string, timezone: string, duration?: number) => {
      dispatch(
        fetchAvailableSlots({ calendarId, date, timezone, duration })
      );
    },
    [dispatch]
  );

  const loadAvailableDates = useCallback(
    (
      calendarId: string,
      startDate?: string,
      endDate?: string,
      duration?: number
    ) => {
      const start = startDate || format(new Date(), 'yyyy-MM-dd');
      const end = endDate || format(addDays(new Date(), 60), 'yyyy-MM-dd');
      dispatch(
        fetchAvailableDates({ calendarId, startDate: start, endDate: end, duration })
      );
    },
    [dispatch]
  );

  return {
    calendars,
    selectedCalendar,
    availabilityRules,
    availableSlots,
    availableDates,
    selectedDate,
    isLoading,
    isSlotsLoading,
    setSelectedCalendar,
    loadRules,
    setSelectedDate,
    loadSlots,
    loadAvailableDates,
  };
}
