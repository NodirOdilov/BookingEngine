/**
 * Booking form component for the public booking flow.
 * Collects invitee information and custom question responses.
 */

import React from 'react';
import { useForm } from 'react-hook-form';
import {
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  ChatBubbleLeftIcon,
} from '@heroicons/react/24/outline';
import { CustomQuestion } from '../../api/services';

interface BookingFormData {
  invitee_name: string;
  invitee_email: string;
  invitee_phone: string;
  invitee_notes: string;
  custom_responses: Record<string, string>;
}

interface BookingFormProps {
  customQuestions: CustomQuestion[];
  onSubmit: (data: BookingFormData) => void;
  isSubmitting: boolean;
  eventTypeName: string;
  selectedTime: string;
}

export default function BookingForm({
  customQuestions,
  onSubmit,
  isSubmitting,
  eventTypeName,
  selectedTime,
}: BookingFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BookingFormData>();

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <p className="text-sm font-medium text-blue-900">{eventTypeName}</p>
        <p className="text-sm text-blue-700 mt-1">{selectedTime}</p>
      </div>

      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Your name *
        </label>
        <div className="relative">
          <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            {...register('invitee_name', { required: 'Name is required' })}
            className={`w-full pl-10 pr-3 py-2.5 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.invitee_name ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="John Smith"
          />
        </div>
        {errors.invitee_name && (
          <p className="mt-1 text-sm text-red-600">
            {errors.invitee_name.message}
          </p>
        )}
      </div>

      {/* Email */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email address *
        </label>
        <div className="relative">
          <EnvelopeIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="email"
            {...register('invitee_email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            })}
            className={`w-full pl-10 pr-3 py-2.5 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.invitee_email ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="john@example.com"
          />
        </div>
        {errors.invitee_email && (
          <p className="mt-1 text-sm text-red-600">
            {errors.invitee_email.message}
          </p>
        )}
      </div>

      {/* Phone (optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Phone number
        </label>
        <div className="relative">
          <PhoneIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="tel"
            {...register('invitee_phone')}
            className="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="+1 (555) 123-4567"
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Additional notes
        </label>
        <div className="relative">
          <ChatBubbleLeftIcon className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
          <textarea
            {...register('invitee_notes')}
            rows={3}
            className="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="Anything you'd like to share before our meeting..."
          />
        </div>
      </div>

      {/* Custom questions */}
      {customQuestions.map((question, idx) => (
        <div key={idx}>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {question.label} {question.required && '*'}
          </label>
          {question.type === 'textarea' ? (
            <textarea
              {...register(`custom_responses.${question.label}`, {
                required: question.required
                  ? `${question.label} is required`
                  : false,
              })}
              rows={3}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          ) : question.type === 'select' ? (
            <select
              {...register(`custom_responses.${question.label}`, {
                required: question.required
                  ? `${question.label} is required`
                  : false,
              })}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select an option</option>
              {question.options?.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          ) : question.type === 'checkbox' ? (
            <div className="flex items-center">
              <input
                type="checkbox"
                {...register(`custom_responses.${question.label}`)}
                className="h-4 w-4 text-blue-600 rounded border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-600">Yes</span>
            </div>
          ) : (
            <input
              type="text"
              {...register(`custom_responses.${question.label}`, {
                required: question.required
                  ? `${question.label} is required`
                  : false,
              })}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          )}
        </div>
      ))}

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center">
            <svg
              className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Scheduling...
          </span>
        ) : (
          'Confirm Booking'
        )}
      </button>
    </form>
  );
}
