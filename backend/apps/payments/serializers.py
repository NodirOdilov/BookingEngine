"""
Serializers for payments app.
"""

from rest_framework import serializers

from .models import Payment, PayoutAccount, Refund


class PaymentSerializer(serializers.ModelSerializer):
    """Full payment serializer."""

    is_successful = serializers.ReadOnlyField()
    refundable_amount = serializers.ReadOnlyField()
    booking_reference = serializers.CharField(
        source="booking.reference", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "booking_reference",
            "payer_email",
            "payer_name",
            "amount",
            "currency",
            "platform_fee",
            "net_amount",
            "payment_method_type",
            "last_four",
            "card_brand",
            "status",
            "paid_at",
            "receipt_url",
            "invoice_number",
            "is_successful",
            "refundable_amount",
            "created_at",
        ]
        read_only_fields = [
            "id", "platform_fee", "net_amount",
            "paid_at", "created_at",
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for initiating a payment (creating a Stripe Payment Intent)."""

    booking_id = serializers.UUIDField()
    payment_method_id = serializers.CharField(required=False, allow_blank=True)

    def validate_booking_id(self, value):
        from apps.bookings.models import Booking
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        if not booking.is_paid:
            raise serializers.ValidationError("This booking does not require payment.")

        if hasattr(booking, "payment") and booking.payment.status == "completed":
            raise serializers.ValidationError("Payment already completed.")

        return value


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for refunds."""

    class Meta:
        model = Refund
        fields = [
            "id",
            "payment",
            "amount",
            "reason",
            "notes",
            "status",
            "refunded_at",
            "created_at",
        ]
        read_only_fields = ["id", "status", "refunded_at", "created_at"]


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for initiating a refund."""

    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.ChoiceField(choices=Refund.REASON_CHOICES, default="other")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        try:
            payment = Payment.objects.get(id=attrs["payment_id"])
        except Payment.DoesNotExist:
            raise serializers.ValidationError({"payment_id": "Payment not found."})

        if payment.status != "completed":
            raise serializers.ValidationError(
                {"payment_id": "Only completed payments can be refunded."}
            )

        if attrs["amount"] > payment.refundable_amount:
            raise serializers.ValidationError({
                "amount": f"Maximum refundable amount is {payment.refundable_amount}."
            })

        return attrs


class PayoutAccountSerializer(serializers.ModelSerializer):
    """Serializer for payout accounts."""

    class Meta:
        model = PayoutAccount
        fields = [
            "id",
            "stripe_account_id",
            "account_status",
            "business_type",
            "country",
            "default_currency",
            "payout_schedule",
            "charges_enabled",
            "payouts_enabled",
            "details_submitted",
            "total_earned",
            "total_paid_out",
            "created_at",
        ]
        read_only_fields = [
            "id", "stripe_account_id", "charges_enabled",
            "payouts_enabled", "details_submitted",
            "total_earned", "total_paid_out", "created_at",
        ]
