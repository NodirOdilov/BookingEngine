/**
 * Settings page with tabs for profile, availability, integrations, and notifications.
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  BellIcon,
  CogIcon,
  LinkIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import { TIMEZONE_OPTIONS } from '../utils/constants';
import toast from 'react-hot-toast';

type SettingsTab = 'profile' | 'integrations' | 'notifications' | 'billing';

const TABS: Array<{ key: SettingsTab; label: string; icon: typeof UserIcon }> = [
  { key: 'profile', label: 'Profile', icon: UserIcon },
  { key: 'integrations', label: 'Integrations', icon: LinkIcon },
  { key: 'notifications', label: 'Notifications', icon: BellIcon },
  { key: 'billing', label: 'Billing', icon: CogIcon },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const { user, updateProfile } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { isDirty, isSubmitting },
  } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      bio: user?.bio || '',
      timezone: user?.timezone || 'America/New_York',
      date_format: user?.date_format || 'MM/DD/YYYY',
      time_format: user?.time_format || '12h',
      welcome_message: user?.welcome_message || '',
    },
  });

  const onSubmitProfile = async (data: Record<string, string>) => {
    const success = await updateProfile(data);
    if (success) {
      toast.success('Profile updated');
    } else {
      toast.error('Failed to update profile');
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Settings</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center pb-3 px-1 border-b-2 text-sm font-medium transition-colors ${
                activeTab === key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Profile tab */}
      {activeTab === 'profile' && (
        <form
          onSubmit={handleSubmit(onSubmitProfile)}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Personal Information
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First name
              </label>
              <input
                {...register('first_name')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last name
              </label>
              <input
                {...register('last_name')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                {...register('phone')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timezone
              </label>
              <select
                {...register('timezone')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                {TIMEZONE_OPTIONS.map((group) => (
                  <optgroup key={group.group} label={group.group}>
                    {group.zones.map((tz) => (
                      <option key={tz.value} value={tz.value}>
                        {tz.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Bio
              </label>
              <textarea
                {...register('bio')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Tell clients a bit about yourself..."
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Welcome message
              </label>
              <textarea
                {...register('welcome_message')}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Message shown on your booking page..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date format
              </label>
              <select
                {...register('date_format')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Time format
              </label>
              <select
                {...register('time_format')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="12h">12 hour</option>
                <option value="24h">24 hour</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={!isDirty || isSubmitting}
              className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      )}

      {/* Integrations tab */}
      {activeTab === 'integrations' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Calendar Integrations
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">G</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Google Calendar
                    </p>
                    <p className="text-xs text-gray-500">
                      Sync bookings and check for conflicts
                    </p>
                  </div>
                </div>
                <button className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50">
                  Connect
                </button>
              </div>
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg">O</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Microsoft Outlook
                    </p>
                    <p className="text-xs text-gray-500">
                      Sync with Outlook Calendar
                    </p>
                  </div>
                </div>
                <button className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50">
                  Connect
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notifications tab */}
      {activeTab === 'notifications' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Notification Preferences
          </h2>
          <div className="space-y-5">
            {[
              { label: 'New booking notifications', desc: 'Get notified when someone books a meeting' },
              { label: 'Booking cancellations', desc: 'Get notified when a booking is cancelled' },
              { label: 'Booking reminders', desc: 'Receive reminders before upcoming meetings' },
              { label: 'Daily digest', desc: 'Daily summary of your upcoming schedule' },
              { label: 'Payment notifications', desc: 'Get notified when you receive a payment' },
            ].map(({ label, desc }) => (
              <div key={label} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{label}</p>
                  <p className="text-xs text-gray-500">{desc}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
                </label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Billing tab */}
      {activeTab === 'billing' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Billing & Plan
          </h2>
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium text-blue-900">Free Plan</p>
            <p className="text-xs text-blue-700 mt-1">
              You are on the free plan. Upgrade to unlock more features.
            </p>
          </div>
          <button className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
            Upgrade Plan
          </button>
        </div>
      )}
    </div>
  );
}
