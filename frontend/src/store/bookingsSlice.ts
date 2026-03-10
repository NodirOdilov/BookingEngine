/**
 * Bookings slice: manages booking list state, filters, and CRUD operations.
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  Booking,
  BookingListParams,
  BookingStats,
  bookingsApi,
} from '../api/bookings';

interface BookingsState {
  items: Booking[];
  selectedBooking: Booking | null;
  stats: BookingStats | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
  isLoading: boolean;
  isStatsLoading: boolean;
  error: string | null;
  filters: BookingListParams;
}

const initialState: BookingsState = {
  items: [],
  selectedBooking: null,
  stats: null,
  totalCount: 0,
  currentPage: 1,
  totalPages: 1,
  isLoading: false,
  isStatsLoading: false,
  error: null,
  filters: {
    time_filter: 'upcoming',
    page: 1,
    page_size: 20,
    ordering: '-start_time',
  },
};

export const fetchBookings = createAsyncThunk(
  'bookings/fetchBookings',
  async (params: BookingListParams | undefined, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { bookings: BookingsState };
      const mergedParams = { ...state.bookings.filters, ...params };
      const { data } = await bookingsApi.list(mergedParams);
      return data;
    } catch {
      return rejectWithValue('Failed to fetch bookings.');
    }
  }
);

export const fetchBookingDetail = createAsyncThunk(
  'bookings/fetchDetail',
  async (id: string, { rejectWithValue }) => {
    try {
      const { data } = await bookingsApi.get(id);
      return data;
    } catch {
      return rejectWithValue('Failed to fetch booking details.');
    }
  }
);

export const fetchBookingStats = createAsyncThunk(
  'bookings/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await bookingsApi.getStats();
      return data;
    } catch {
      return rejectWithValue('Failed to fetch booking stats.');
    }
  }
);

export const confirmBooking = createAsyncThunk(
  'bookings/confirm',
  async (id: string, { rejectWithValue }) => {
    try {
      const { data } = await bookingsApi.confirm(id);
      return data;
    } catch {
      return rejectWithValue('Failed to confirm booking.');
    }
  }
);

export const cancelBooking = createAsyncThunk(
  'bookings/cancel',
  async (
    { id, reason, notes }: { id: string; reason: string; notes?: string },
    { rejectWithValue }
  ) => {
    try {
      const { data } = await bookingsApi.cancel(id, reason, notes);
      return data;
    } catch {
      return rejectWithValue('Failed to cancel booking.');
    }
  }
);

const bookingsSlice = createSlice({
  name: 'bookings',
  initialState,
  reducers: {
    setFilters(state, action: PayloadAction<Partial<BookingListParams>>) {
      state.filters = { ...state.filters, ...action.payload, page: 1 };
    },
    setPage(state, action: PayloadAction<number>) {
      state.filters.page = action.payload;
    },
    clearSelectedBooking(state) {
      state.selectedBooking = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBookings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchBookings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.results;
        state.totalCount = action.payload.count;
        state.currentPage = action.payload.current_page;
        state.totalPages = action.payload.total_pages;
      })
      .addCase(fetchBookings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchBookingDetail.fulfilled, (state, action) => {
        state.selectedBooking = action.payload;
      })
      .addCase(fetchBookingStats.pending, (state) => {
        state.isStatsLoading = true;
      })
      .addCase(fetchBookingStats.fulfilled, (state, action) => {
        state.isStatsLoading = false;
        state.stats = action.payload;
      })
      .addCase(confirmBooking.fulfilled, (state, action) => {
        const idx = state.items.findIndex((b) => b.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
        if (state.selectedBooking?.id === action.payload.id) {
          state.selectedBooking = action.payload;
        }
      })
      .addCase(cancelBooking.fulfilled, (state, action) => {
        const idx = state.items.findIndex((b) => b.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
        if (state.selectedBooking?.id === action.payload.id) {
          state.selectedBooking = action.payload;
        }
      });
  },
});

export const { setFilters, setPage, clearSelectedBooking, clearError } =
  bookingsSlice.actions;
export default bookingsSlice.reducer;
