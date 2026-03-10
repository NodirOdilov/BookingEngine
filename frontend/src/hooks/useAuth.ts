/**
 * Custom hook for authentication operations.
 * Provides login, logout, registration, and profile management.
 */

import { useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store';
import {
  fetchProfile,
  login as loginAction,
  logout as logoutAction,
  register as registerAction,
  updateProfile as updateProfileAction,
} from '../store/authSlice';
import { LoginPayload, RegisterPayload, User } from '../api/auth';

export function useAuth() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, error } = useAppSelector(
    (state) => state.auth
  );

  useEffect(() => {
    if (isAuthenticated && !user) {
      dispatch(fetchProfile());
    }
  }, [dispatch, isAuthenticated, user]);

  const login = useCallback(
    async (credentials: LoginPayload) => {
      const result = await dispatch(loginAction(credentials));
      if (loginAction.fulfilled.match(result)) {
        navigate('/dashboard');
        return true;
      }
      return false;
    },
    [dispatch, navigate]
  );

  const register = useCallback(
    async (data: RegisterPayload) => {
      const result = await dispatch(registerAction(data));
      if (registerAction.fulfilled.match(result)) {
        navigate('/login?registered=true');
        return true;
      }
      return false;
    },
    [dispatch, navigate]
  );

  const logout = useCallback(() => {
    dispatch(logoutAction());
    navigate('/login');
  }, [dispatch, navigate]);

  const updateProfile = useCallback(
    async (data: Partial<User>) => {
      const result = await dispatch(updateProfileAction(data));
      return updateProfileAction.fulfilled.match(result);
    },
    [dispatch]
  );

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    updateProfile,
  };
}
