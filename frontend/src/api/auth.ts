/**
 * Authentication API module.
 * Handles login, registration, profile management, and organization endpoints.
 */

import apiClient from './client';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  slug: string;
  phone: string;
  avatar: string | null;
  bio: string;
  timezone: string;
  date_format: string;
  time_format: string;
  welcome_message: string;
  is_email_verified: boolean;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  timezone?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo: string | null;
  website: string;
  owner: { id: string; email: string; full_name: string };
  plan: string;
  member_count: number;
  is_active: boolean;
  created_at: string;
}

export const authApi = {
  login: (data: LoginPayload) =>
    apiClient.post<LoginResponse>('/auth/token/', data),

  register: (data: RegisterPayload) =>
    apiClient.post('/auth/register/', data),

  refreshToken: (refresh: string) =>
    apiClient.post('/auth/token/refresh/', { refresh }),

  getProfile: () =>
    apiClient.get<User>('/auth/profile/'),

  updateProfile: (data: Partial<User>) =>
    apiClient.patch<User>('/auth/profile/', data),

  changePassword: (oldPassword: string, newPassword: string, confirm: string) =>
    apiClient.put('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: confirm,
    }),

  getPublicProfile: (slug: string) =>
    apiClient.get<User>(`/auth/users/${slug}/`),
};

export const organizationsApi = {
  list: () =>
    apiClient.get<Organization[]>('/auth/organizations/'),

  get: (id: string) =>
    apiClient.get<Organization>(`/auth/organizations/${id}/`),

  create: (data: { name: string; website?: string; default_timezone?: string }) =>
    apiClient.post<Organization>('/auth/organizations/', data),

  update: (id: string, data: Partial<Organization>) =>
    apiClient.patch<Organization>(`/auth/organizations/${id}/`, data),

  getMembers: (id: string) =>
    apiClient.get(`/auth/organizations/${id}/members/`),

  inviteMember: (id: string, email: string, role = 'member') =>
    apiClient.post(`/auth/organizations/${id}/invite/`, { email, role }),

  removeMember: (id: string, memberId: string) =>
    apiClient.post(`/auth/organizations/${id}/remove-member/`, { member_id: memberId }),
};
