/**
 * Main sidebar navigation component.
 * Displays navigation links, user info, and organization switcher.
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  CalendarIcon,
  ClockIcon,
  CogIcon,
  HomeIcon,
  RectangleStackIcon,
  UserGroupIcon,
  ChevronLeftIcon,
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '../../store';
import { toggleSidebarCollapse } from '../../store/uiSlice';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Calendar', href: '/calendar', icon: CalendarIcon },
  { name: 'Bookings', href: '/bookings', icon: ClockIcon },
  { name: 'Services', href: '/services', icon: RectangleStackIcon },
  { name: 'Clients', href: '/clients', icon: UserGroupIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

export default function Sidebar() {
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { sidebarCollapsed } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);

  const isActive = (href: string) => location.pathname.startsWith(href);

  return (
    <aside
      className={`flex flex-col bg-white border-r border-gray-200 transition-all duration-200 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo area */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
        {!sidebarCollapsed && (
          <Link to="/dashboard" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <CalendarIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-gray-900">
              BookingEngine
            </span>
          </Link>
        )}
        <button
          onClick={() => dispatch(toggleSidebarCollapse())}
          className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500"
          aria-label="Toggle sidebar"
        >
          <ChevronLeftIcon
            className={`w-5 h-5 transition-transform ${
              sidebarCollapsed ? 'rotate-180' : ''
            }`}
          />
        </button>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              }`}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <item.icon
                className={`flex-shrink-0 w-5 h-5 ${
                  active ? 'text-blue-600' : 'text-gray-400'
                }`}
              />
              {!sidebarCollapsed && (
                <span className="ml-3">{item.name}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User info */}
      {user && !sidebarCollapsed && (
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {user.avatar ? (
                <img
                  className="w-8 h-8 rounded-full"
                  src={user.avatar}
                  alt={user.full_name}
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">
                    {user.first_name[0]}
                    {user.last_name[0]}
                  </span>
                </div>
              )}
            </div>
            <div className="ml-3 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user.full_name}
              </p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
