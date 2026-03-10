/**
 * Services (Event Types) page.
 * Lists all event types with create, edit, duplicate, and delete actions.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, RectangleStackIcon } from '@heroicons/react/24/outline';
import ServiceCard from '../components/services/ServiceCard';
import { EventType, eventTypesApi } from '../api/services';
import toast from 'react-hot-toast';

export default function ServicesPage() {
  const navigate = useNavigate();
  const [services, setServices] = useState<EventType[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchServices = useCallback(async () => {
    try {
      setIsLoading(true);
      const { data } = await eventTypesApi.list();
      setServices(data);
    } catch {
      toast.error('Failed to load services');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const handleEdit = (service: EventType) => {
    navigate(`/services/${service.id}/edit`);
  };

  const handleDuplicate = async (id: string) => {
    try {
      await eventTypesApi.duplicate(id);
      toast.success('Service duplicated');
      fetchServices();
    } catch {
      toast.error('Failed to duplicate');
    }
  };

  const handleToggleActive = async (id: string) => {
    try {
      const { data } = await eventTypesApi.toggleActive(id);
      toast.success(data.is_active ? 'Service activated' : 'Service deactivated');
      fetchServices();
    } catch {
      toast.error('Failed to toggle status');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this service?')) return;
    try {
      await eventTypesApi.delete(id);
      toast.success('Service deleted');
      fetchServices();
    } catch {
      toast.error('Failed to delete');
    }
  };

  const handleCopyLink = (url: string) => {
    const fullUrl = `${window.location.origin}${url}`;
    navigator.clipboard.writeText(fullUrl);
    toast.success('Booking link copied');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Services</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create and manage the event types your clients can book.
          </p>
        </div>
        <button
          onClick={() => navigate('/services/new')}
          className="inline-flex items-center px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Service
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : services.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <RectangleStackIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-3 text-sm font-semibold text-gray-900">
            No services yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Create your first event type to start accepting bookings.
          </p>
          <button
            onClick={() => navigate('/services/new')}
            className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Create Service
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {services.map((service) => (
            <ServiceCard
              key={service.id}
              service={service}
              onEdit={handleEdit}
              onDuplicate={handleDuplicate}
              onToggleActive={handleToggleActive}
              onDelete={handleDelete}
              onCopyLink={handleCopyLink}
            />
          ))}
        </div>
      )}
    </div>
  );
}
