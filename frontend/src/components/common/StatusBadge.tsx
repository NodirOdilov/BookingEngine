/**
 * Reusable status badge component.
 * Renders a colored badge based on booking or payment status.
 */

import React from 'react';
import {
  BOOKING_STATUS_COLORS,
  BOOKING_STATUS_LABELS,
} from '../../utils/constants';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export default function StatusBadge({
  status,
  size = 'sm',
  showDot = true,
}: StatusBadgeProps) {
  const style = BOOKING_STATUS_COLORS[status] || {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    dot: 'bg-gray-400',
  };

  const label = BOOKING_STATUS_LABELS[status] || status;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2 h-2',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${style.bg} ${style.text} ${sizeClasses[size]}`}
    >
      {showDot && (
        <span
          className={`${dotSizes[size]} rounded-full ${style.dot} mr-1.5`}
        />
      )}
      {label}
    </span>
  );
}
