/**
 * Calendar slice: manages calendars, availability rules, and time slots.
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  AvailabilityRule,
  AvailableSlotsResponse,
  BlockedTime,
  Calendar,
  calendarsApi,
  TimeSlot,
} from '../api/calendars';

interface CalendarState {
  calendars: Calendar[];
  selectedCalendar: Calendar | null;
  availabilityRules: AvailabilityRule[];
  blockedTimes: BlockedTime[];
  availableSlots: TimeSlot[];
  availableDates: string[];
  selectedDate: string | null;
  isLoading: boolean;
  isSlotsLoading: boolean;
  error: string | null;
}

const initialState: CalendarState = {
  calendars: [],
  selectedCalendar: null,
  availabilityRules: [],
  blockedTimes: [],
  availableSlots: [],
  availableDates: [],
  selectedDate: null,
  isLoading: false,
  isSlotsLoading: false,
  error: null,
};

export const fetchCalendars = createAsyncThunk(
  'calendar/fetchCalendars',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await calendarsApi.list();
      return data;
    } catch {
      return rejectWithValue('Failed to fetch calendars.');
    }
  }
);

export const fetchAvailabilityRules = createAsyncThunk(
  'calendar/fetchRules',
  async (calendarId: string, { rejectWithValue }) => {
    try {
      const { data } = await calendarsApi.getAvailabilityRules(calendarId);
      return data;
    } catch {
      return rejectWithValue('Failed to fetch availability rules.');
    }
  }
);

export const fetchAvailableSlots = createAsyncThunk(
  'calendar/fetchSlots',
  async (
    params: {
      calendarId: string;
      date: string;
      timezone: string;
      duration?: number;
    },
    { rejectWithValue }
  ) => {
    try {
      const { data } = await calendarsApi.getAvailableSlots(
        params.calendarId,
        params.date,
        params.timezone,
        params.duration
      );
      return data;
    } catch {
      return rejectWithValue('Failed to fetch available slots.');
    }
  }
);

export const fetchAvailableDates = createAsyncThunk(
  'calendar/fetchDates',
  async (
    params: {
      calendarId: string;
      startDate: string;
      endDate: string;
      duration?: number;
    },
    { rejectWithValue }
  ) => {
    try {
      const { data } = await calendarsApi.getAvailableDates(
        params.calendarId,
        params.startDate,
        params.endDate,
        params.duration
      );
      return data.available_dates;
    } catch {
      return rejectWithValue('Failed to fetch available dates.');
    }
  }
);

const calendarSlice = createSlice({
  name: 'calendar',
  initialState,
  reducers: {
    selectCalendar(state, action: PayloadAction<Calendar>) {
      state.selectedCalendar = action.payload;
    },
    selectDate(state, action: PayloadAction<string | null>) {
      state.selectedDate = action.payload;
      state.availableSlots = [];
    },
    clearSlots(state) {
      state.availableSlots = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCalendars.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchCalendars.fulfilled, (state, action) => {
        state.isLoading = false;
        state.calendars = action.payload;
        if (!state.selectedCalendar && action.payload.length > 0) {
          state.selectedCalendar =
            action.payload.find((c) => c.is_default) || action.payload[0];
        }
      })
      .addCase(fetchCalendars.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchAvailabilityRules.fulfilled, (state, action) => {
        state.availabilityRules = action.payload;
      })
      .addCase(fetchAvailableSlots.pending, (state) => {
        state.isSlotsLoading = true;
      })
      .addCase(fetchAvailableSlots.fulfilled, (state, action) => {
        state.isSlotsLoading = false;
        state.availableSlots = action.payload.slots;
      })
      .addCase(fetchAvailableSlots.rejected, (state) => {
        state.isSlotsLoading = false;
      })
      .addCase(fetchAvailableDates.fulfilled, (state, action) => {
        state.availableDates = action.payload;
      });
  },
});

export const { selectCalendar, selectDate, clearSlots } = calendarSlice.actions;
export default calendarSlice.reducer;
