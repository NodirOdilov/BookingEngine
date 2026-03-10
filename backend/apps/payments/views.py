"""
Views for payments app: payment processing, refunds, payout accounts, Stripe webhooks.
"""

import logging

from django.conf import settings
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Payment, PayoutAccount, Refund
from .serializers import (
    PaymentCreateSerializer,
    PaymentSerializer,
    PayoutAccountSerializer,
    RefundCreateSerializer,
    RefundSerializer,
)
from .services import StripeService

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve payments for the authenticated user."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            booking__host=self.request.user
        ).select_related("booking")

    @action(detail=False, methods=["post"], url_path="create-intent")
    def create_intent(self, request):
        """Create a Stripe Payment Intent for a booking."""
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.bookings.models import Booking
        booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

        stripe_service = StripeService()
        try:
            intent_data = stripe_service.create_payment_intent(
                amount=booking.payment_amount,
                currency=booking.payment_currency,
                booking=booking,
                payment_method_id=serializer.validated_data.get("payment_method_id"),
            )

            # Create or update payment record
            payment, created = Payment.objects.update_or_create(
                booking=booking,
                defaults={
                    "payer_email": booking.invitee_email,
                    "payer_name": booking.invitee_name,
                    "amount": booking.payment_amount,
                    "currency": booking.payment_currency,
                    "stripe_payment_intent_id": intent_data["payment_intent_id"],
                    "status": "processing",
                },
            )

            return Response({
                "client_secret": intent_data["client_secret"],
                "payment_intent_id": intent_data["payment_intent_id"],
                "payment_id": str(payment.id),
            })

        except Exception as exc:
            logger.error("Payment intent creation failed: %s", str(exc))
            return Response(
                {"detail": "Failed to create payment. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get payment summary statistics."""
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        payments = Payment.objects.filter(booking__host=request.user)

        total_revenue = payments.filter(
            status="completed"
        ).aggregate(total=Sum("net_amount"))["total"] or 0

        monthly_revenue = payments.filter(
            status="completed",
            paid_at__gte=month_start,
        ).aggregate(total=Sum("net_amount"))["total"] or 0

        pending_payments = payments.filter(
            status__in=["pending", "processing"]
        ).count()

        total_refunded = Refund.objects.filter(
            payment__booking__host=request.user,
            status="completed",
        ).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "total_revenue": str(total_revenue),
            "monthly_revenue": str(monthly_revenue),
            "pending_payments": pending_payments,
            "total_refunded": str(total_refunded),
            "currency": "USD",
        })


class RefundViewSet(viewsets.ModelViewSet):
    """Manage refunds for payments."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return RefundCreateSerializer
        return RefundSerializer

    def get_queryset(self):
        return Refund.objects.filter(
            payment__booking__host=self.request.user
        ).select_related("payment")

    def create(self, request, *args, **kwargs):
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = Payment.objects.get(id=serializer.validated_data["payment_id"])
        stripe_service = StripeService()

        try:
            stripe_refund = stripe_service.create_refund(
                payment_intent_id=payment.stripe_payment_intent_id,
                amount=serializer.validated_data["amount"],
            )

            refund = Refund.objects.create(
                payment=payment,
                amount=serializer.validated_data["amount"],
                reason=serializer.validated_data.get("reason", "other"),
                notes=serializer.validated_data.get("notes", ""),
                stripe_refund_id=stripe_refund.get("refund_id", ""),
                status="completed",
                initiated_by=request.user,
            )

            # Update payment status
            if payment.refundable_amount <= 0:
                payment.status = "refunded"
            else:
                payment.status = "partially_refunded"
            payment.save(update_fields=["status", "updated_at"])

            return Response(
                RefundSerializer(refund).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.error("Refund failed: %s", str(exc))
            return Response(
                {"detail": "Refund processing failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PayoutAccountView(generics.RetrieveAPIView):
    """Retrieve the authenticated user's payout account."""

    serializer_class = PayoutAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        account, created = PayoutAccount.objects.get_or_create(
            user=self.request.user,
            defaults={"stripe_account_id": ""},
        )
        return account


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    Processes payment confirmations, failures, and refund updates.
    """
    import stripe

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return Response(
            {"detail": "Invalid payload."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except stripe.error.SignatureVerificationError:
        return Response(
            {"detail": "Invalid signature."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        _handle_payment_succeeded(data)
    elif event_type == "payment_intent.payment_failed":
        _handle_payment_failed(data)
    elif event_type == "charge.refunded":
        _handle_charge_refunded(data)

    return Response({"status": "ok"})


def _handle_payment_succeeded(data):
    """Process successful payment."""
    from django.utils import timezone

    payment_intent_id = data["id"]
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.stripe_charge_id = data.get("latest_charge", "")

        # Calculate net amount (after platform fee)
        platform_fee_rate = 0.029  # 2.9% example
        payment.platform_fee = payment.amount * platform_fee_rate
        payment.net_amount = payment.amount - payment.platform_fee

        # Extract card details
        charges = data.get("charges", {}).get("data", [])
        if charges:
            payment_method = charges[0].get("payment_method_details", {}).get("card", {})
            payment.last_four = payment_method.get("last4", "")
            payment.card_brand = payment_method.get("brand", "")
            payment.receipt_url = charges[0].get("receipt_url", "")

        payment.save()

        # Update booking payment status
        payment.booking.payment_status = "completed"
        payment.booking.save(update_fields=["payment_status", "updated_at"])

        logger.info("Payment completed for booking %s", payment.booking.reference)

    except Payment.DoesNotExist:
        logger.warning("Payment not found for intent: %s", payment_intent_id)


def _handle_payment_failed(data):
    """Process failed payment."""
    from django.utils import timezone

    payment_intent_id = data["id"]
    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = "failed"
        payment.failed_at = timezone.now()
        payment.failure_reason = data.get("last_payment_error", {}).get("message", "")
        payment.save()

        payment.booking.payment_status = "failed"
        payment.booking.save(update_fields=["payment_status", "updated_at"])

        logger.info("Payment failed for booking %s", payment.booking.reference)

    except Payment.DoesNotExist:
        logger.warning("Payment not found for failed intent: %s", payment_intent_id)


def _handle_charge_refunded(data):
    """Process charge refund event."""
    logger.info("Charge refunded: %s", data.get("id"))
