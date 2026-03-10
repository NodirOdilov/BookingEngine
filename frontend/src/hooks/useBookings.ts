/**
 * Custom hook for booking operations.
 * Provides a clean interface for components to interact with booking state and API.
 */

import { useCallback, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
  cancelBooking,
  confirmBooking,
  fetchBookingDetail,
  fetchBookings,
  fetchBookingStats,
  setFilters,
  setPage,
} from '../store/bookingsSlice';
import { BookingListParams, BookingStatus } from '../api/bookings';

export function useBookings(autoFetch = true) {
  const dispatch = useAppDispatch();
  const {
    items,
    selectedBooking,
    stats,
    totalCount,
    currentPage,
    totalPages,
    isLoading,
    isStatsLoading,
    error,
    filters,
  } = useAppSelector((state) => state.bookings);

  useEffect(() => {
    if (autoFetch) {
      dispatch(fetchBookings(filters));
    }
  }, [dispatch, autoFetch, filters]);

  const refresh = useCallback(() => {
    dispatch(fetchBookings(filters));
  }, [dispatch, filters]);

  const loadStats = useCallback(() => {
    dispatch(fetchBookingStats());
  }, [dispatch]);

  const loadDetail = useCallback(
    (id: string) => {
      dispatch(fetchBookingDetail(id));
    },
    [dispatch]
  );

  const confirm = useCallback(
    async (id: string) => {
      await dispatch(confirmBooking(id));
      refresh();
    },
    [dispatch, refresh]
  );

  const cancel = useCallback(
    async (id: string, reason: string, notes?: string) => {
      await dispatch(cancelBooking({ id, reason, notes }));
      refresh();
    },
    [dispatch, refresh]
  );

  const updateFilters = useCallback(
    (newFilters: Partial<BookingListParams>) => {
      dispatch(setFilters(newFilters));
    },
    [dispatch]
  );

  const goToPage = useCallback(
    (page: number) => {
      dispatch(setPage(page));
      dispatch(fetchBookings({ ...filters, page }));
    },
    [dispatch, filters]
  );

  const filterByStatus = useCallback(
    (status: BookingStatus | undefined) => {
      dispatch(setFilters({ status }));
    },
    [dispatch]
  );

  return {
    bookings: items,
    selectedBooking,
    stats,
    totalCount,
    currentPage,
    totalPages,
    isLoading,
    isStatsLoading,
    error,
    filters,
    refresh,
    loadStats,
    loadDetail,
    confirm,
    cancel,
    updateFilters,
    goToPage,
    filterByStatus,
  };
}
