/**
 * Service (Event Type) card component.
 * Displays event type info with actions in the services management view.
 */

import React from 'react';
import {
  ClockIcon,
  CurrencyDollarIcon,
  DocumentDuplicateIcon,
  EllipsisVerticalIcon,
  EyeIcon,
  LinkIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { EventType } from '../../api/services';
import { formatDuration } from '../../utils/dateUtils';
import { BOOKING_STATUS_COLORS } from '../../utils/constants';

interface ServiceCardProps {
  service: EventType;
  onEdit: (service: EventType) => void;
  onDuplicate: (id: string) => void;
  onToggleActive: (id: string) => void;
  onDelete: (id: string) => void;
  onCopyLink: (url: string) => void;
}

export default function ServiceCard({
  service,
  onEdit,
  onDuplicate,
  onToggleActive,
  onDelete,
  onCopyLink,
}: ServiceCardProps) {
  const [menuOpen, setMenuOpen] = React.useState(false);

  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow ${
        !service.is_active ? 'opacity-60' : ''
      }`}
    >
      {/* Color bar and header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div
            className="w-3 h-12 rounded-full flex-shrink-0"
            style={{ backgroundColor: service.color }}
          />
          <div>
            <h3 className="text-base font-semibold text-gray-900">
              {service.name}
            </h3>
            {service.description && (
              <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                {service.description}
              </p>
            )}
          </div>
        </div>

        {/* Actions menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400"
          >
            <EllipsisVerticalIcon className="w-5 h-5" />
          </button>

          {menuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-1">
                <button
                  onClick={() => {
                    onEdit(service);
                    setMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Edit
                </button>
                <button
                  onClick={() => {
                    onDuplicate(service.id);
                    setMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <DocumentDuplicateIcon className="w-4 h-4 mr-2" />
                  Duplicate
                </button>
                <button
                  onClick={() => {
                    onCopyLink(service.booking_url);
                    setMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <LinkIcon className="w-4 h-4 mr-2" />
                  Copy Link
                </button>
                <button
                  onClick={() => {
                    onToggleActive(service.id);
                    setMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <EyeIcon className="w-4 h-4 mr-2" />
                  {service.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <hr className="my-1" />
                <button
                  onClick={() => {
                    onDelete(service.id);
                    setMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <TrashIcon className="w-4 h-4 mr-2" />
                  Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
        <div className="flex items-center">
          <ClockIcon className="w-4 h-4 mr-1" />
          {formatDuration(service.duration)}
        </div>
        {service.is_paid && (
          <div className="flex items-center">
            <CurrencyDollarIcon className="w-4 h-4 mr-1" />
            {service.price} {service.currency}
          </div>
        )}
        <span className="capitalize text-xs px-2 py-0.5 rounded-full bg-gray-100">
          {service.scheduling_type.replace('_', ' ')}
        </span>
      </div>

      {/* Status and link */}
      <div className="mt-4 flex items-center justify-between">
        <span
          className={`inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full ${
            service.is_active
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
              service.is_active ? 'bg-green-500' : 'bg-gray-400'
            }`}
          />
          {service.is_active ? 'Active' : 'Inactive'}
        </span>
        <button
          onClick={() => onCopyLink(service.booking_url)}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          Copy booking link
        </button>
      </div>
    </div>
  );
}
