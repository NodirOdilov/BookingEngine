"""
Custom exception handling for BookingEngine API.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class BookingConflictError(APIException):
    """Raised when a booking conflicts with an existing one."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The requested time slot is no longer available."
    default_code = "booking_conflict"


class SlotUnavailableError(APIException):
    """Raised when a requested slot is not available."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The selected time slot is not available."
    default_code = "slot_unavailable"


class PaymentRequiredError(APIException):
    """Raised when payment is required but not completed."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Payment is required to complete this booking."
    default_code = "payment_required"


class IntegrationError(APIException):
    """Raised when an external integration fails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "External service integration error."
    default_code = "integration_error"


class CalendarSyncError(APIException):
    """Raised when calendar synchronization fails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Calendar synchronization failed."
    default_code = "calendar_sync_error"


class BookingCancellationError(APIException):
    """Raised when a booking cannot be cancelled."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This booking cannot be cancelled."
    default_code = "cancellation_error"


class ReschedulingError(APIException):
    """Raised when a booking cannot be rescheduled."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This booking cannot be rescheduled."
    default_code = "rescheduling_error"


def custom_exception_handler(exc, context):
    """
    Custom exception handler that extends DRF's default handler.
    Converts Django validation errors, adds request metadata, and logs errors.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = ValidationError(detail=exc.message_dict)
        else:
            exc = ValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": True,
            "status_code": response.status_code,
        }

        if isinstance(response.data, dict):
            error_payload["detail"] = response.data.get(
                "detail", response.data
            )
            if "code" in response.data:
                error_payload["code"] = response.data["code"]
        elif isinstance(response.data, list):
            error_payload["detail"] = response.data
        else:
            error_payload["detail"] = str(response.data)

        # Add error code for custom exceptions
        if hasattr(exc, "default_code"):
            error_payload["code"] = exc.default_code

        response.data = error_payload

        # Log server errors
        if response.status_code >= 500:
            view = context.get("view")
            logger.error(
                "Server error in %s: %s",
                view.__class__.__name__ if view else "unknown",
                str(exc),
                exc_info=True,
            )
    else:
        # Unhandled exception
        logger.error(
            "Unhandled exception: %s",
            str(exc),
            exc_info=True,
        )

    return response
