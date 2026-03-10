/**
 * UI slice: manages global UI state like sidebar, modals, theme preferences.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ModalState {
  isOpen: boolean;
  type: string | null;
  data: Record<string, unknown> | null;
}

interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  modal: ModalState;
  toastQueue: Array<{
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
  }>;
  calendarView: 'day' | 'week' | 'month';
  bookingView: 'list' | 'board';
}

const initialState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  theme: (localStorage.getItem('theme') as UIState['theme']) || 'light',
  modal: { isOpen: false, type: null, data: null },
  toastQueue: [],
  calendarView: 'week',
  bookingView: 'list',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    toggleSidebarCollapse(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setTheme(state, action: PayloadAction<UIState['theme']>) {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
    },
    openModal(
      state,
      action: PayloadAction<{ type: string; data?: Record<string, unknown> }>
    ) {
      state.modal = {
        isOpen: true,
        type: action.payload.type,
        data: action.payload.data || null,
      };
    },
    closeModal(state) {
      state.modal = { isOpen: false, type: null, data: null };
    },
    addToast(
      state,
      action: PayloadAction<{
        type: 'success' | 'error' | 'info' | 'warning';
        message: string;
      }>
    ) {
      state.toastQueue.push({
        id: Date.now().toString(),
        ...action.payload,
      });
    },
    removeToast(state, action: PayloadAction<string>) {
      state.toastQueue = state.toastQueue.filter((t) => t.id !== action.payload);
    },
    setCalendarView(state, action: PayloadAction<UIState['calendarView']>) {
      state.calendarView = action.payload;
    },
    setBookingView(state, action: PayloadAction<UIState['bookingView']>) {
      state.bookingView = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  toggleSidebarCollapse,
  setTheme,
  openModal,
  closeModal,
  addToast,
  removeToast,
  setCalendarView,
  setBookingView,
} = uiSlice.actions;
export default uiSlice.reducer;
