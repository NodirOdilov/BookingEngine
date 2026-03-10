"""
Payment models: Payment, Refund, PayoutAccount.
Handles payment processing for paid event types via Stripe.
"""

import uuid

from django.conf import settings
from django.db import models


class Payment(models.Model):
    """
    Tracks payment for a booking.
    Integrated with Stripe for payment processing.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
        ("partially_refunded", "Partially Refunded"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("card", "Credit/Debit Card"),
        ("bank_transfer", "Bank Transfer"),
        ("paypal", "PayPal"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    payer_email = models.EmailField()
    payer_name = models.CharField(max_length=255)

    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Platform fee deducted from the payment",
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount after platform fee",
    )

    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    payment_method_type = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="card",
    )
    last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # Receipt
    receipt_url = models.URLField(blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        verbose_name = "payment"
        verbose_name_plural = "payments"

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} ({self.status})"

    @property
    def is_successful(self):
        return self.status == "completed"

    @property
    def refundable_amount(self):
        refunded = self.refunds.filter(
            status="completed"
        ).aggregate(total=models.Sum("amount"))["total"] or 0
        return self.amount - refunded


class Refund(models.Model):
    """Tracks refunds issued for payments."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    REASON_CHOICES = [
        ("cancellation", "Booking Cancellation"),
        ("no_show", "No Show"),
        ("dissatisfied", "Customer Dissatisfied"),
        ("duplicate", "Duplicate Payment"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default="other")
    notes = models.TextField(blank=True)

    stripe_refund_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "refund"
        verbose_name_plural = "refunds"

    def __str__(self):
        return f"Refund {self.amount} {self.payment.currency} for {self.payment.id}"


class PayoutAccount(models.Model):
    """
    User's connected Stripe account for receiving payouts.
    Stores Stripe Connect account info.
    """

    ACCOUNT_STATUS_CHOICES = [
        ("pending", "Pending Setup"),
        ("active", "Active"),
        ("restricted", "Restricted"),
        ("disabled", "Disabled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payout_account",
    )
    stripe_account_id = models.CharField(max_length=255, unique=True)
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default="pending",
    )

    # Account details
    business_type = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=2, default="US")
    default_currency = models.CharField(max_length=3, default="USD")

    # Payout schedule
    payout_schedule = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("manual", "Manual"),
        ],
        default="daily",
    )

    charges_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)
    details_submitted = models.BooleanField(default=False)

    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid_out = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "payout account"
        verbose_name_plural = "payout accounts"

    def __str__(self):
        return f"Payout Account: {self.user.email} ({self.account_status})"
