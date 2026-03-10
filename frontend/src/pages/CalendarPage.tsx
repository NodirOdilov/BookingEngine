/**
 * Calendar page for managing availability.
 * Shows the provider's calendar with availability rules, blocked times, and bookings.
 */

import React, { useEffect, useState } from 'react';
import {
  CalendarIcon,
  ClockIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useCalendar } from '../hooks/useCalendar';
import { useAppSelector } from '../store';
import { calendarsApi, AvailabilityRule } from '../api/calendars';
import { DAYS_OF_WEEK } from '../utils/constants';
import toast from 'react-hot-toast';

export default function CalendarPage() {
  const { user } = useAppSelector((state) => state.auth);
  const {
    calendars,
    selectedCalendar,
    availabilityRules,
    isLoading,
    setSelectedCalendar,
    loadRules,
  } = useCalendar();

  const [isAddingRule, setIsAddingRule] = useState(false);
  const [newRule, setNewRule] = useState({
    day_of_week: 0,
    start_time: '09:00',
    end_time: '17:00',
  });

  useEffect(() => {
    if (selectedCalendar) {
      loadRules(selectedCalendar.id);
    }
  }, [selectedCalendar, loadRules]);

  const handleAddRule = async () => {
    if (!selectedCalendar) return;
    try {
      await calendarsApi.createAvailabilityRule(selectedCalendar.id, {
        rule_type: 'weekly',
        day_of_week: newRule.day_of_week,
        start_time: newRule.start_time,
        end_time: newRule.end_time,
        is_available: true,
      });
      loadRules(selectedCalendar.id);
      setIsAddingRule(false);
      toast.success('Availability rule added');
    } catch {
      toast.error('Failed to add rule');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await calendarsApi.deleteAvailabilityRule(ruleId);
      if (selectedCalendar) loadRules(selectedCalendar.id);
      toast.success('Rule deleted');
    } catch {
      toast.error('Failed to delete rule');
    }
  };

  // Group rules by day
  const rulesByDay = DAYS_OF_WEEK.map((day, idx) => ({
    day,
    dayIndex: idx,
    rules: availabilityRules.filter(
      (r) => r.rule_type === 'weekly' && r.day_of_week === idx
    ),
  }));

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your availability and scheduling preferences.
          </p>
        </div>
      </div>

      {/* Calendar selector */}
      {calendars.length > 1 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Calendar
          </label>
          <div className="flex space-x-2">
            {calendars.map((cal) => (
              <button
                key={cal.id}
                onClick={() => setSelectedCalendar(cal)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  selectedCalendar?.id === cal.id
                    ? 'border-blue-600 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span
                  className="inline-block w-2 h-2 rounded-full mr-2"
                  style={{ backgroundColor: cal.color }}
                />
                {cal.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Weekly availability */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Weekly Availability
          </h2>
          <button
            onClick={() => setIsAddingRule(true)}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Rule
          </button>
        </div>

        <div className="divide-y divide-gray-100">
          {rulesByDay.map(({ day, dayIndex, rules }) => (
            <div key={day} className="px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <div className="w-24">
                    <span className="text-sm font-medium text-gray-900">
                      {day}
                    </span>
                  </div>
                  <div className="space-y-1">
                    {rules.length === 0 ? (
                      <span className="text-sm text-gray-400">Unavailable</span>
                    ) : (
                      rules.map((rule) => (
                        <div
                          key={rule.id}
                          className="flex items-center space-x-2"
                        >
                          <ClockIcon className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-700">
                            {rule.start_time} - {rule.end_time}
                          </span>
                          <button
                            onClick={() => handleDeleteRule(rule.id)}
                            className="p-0.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500"
                          >
                            <XMarkIcon className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add rule modal */}
      {isAddingRule && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Add Availability Rule
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Day of week
                </label>
                <select
                  value={newRule.day_of_week}
                  onChange={(e) =>
                    setNewRule({ ...newRule, day_of_week: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  {DAYS_OF_WEEK.map((day, idx) => (
                    <option key={day} value={idx}>
                      {day}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start time
                  </label>
                  <input
                    type="time"
                    value={newRule.start_time}
                    onChange={(e) =>
                      setNewRule({ ...newRule, start_time: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End time
                  </label>
                  <input
                    type="time"
                    value={newRule.end_time}
                    onChange={(e) =>
                      setNewRule({ ...newRule, end_time: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsAddingRule(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleAddRule}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                Add Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
