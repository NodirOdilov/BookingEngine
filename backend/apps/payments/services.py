"""
Stripe payment service for BookingEngine.
Handles Payment Intent creation, refunds, and Connect account management.
"""

import logging
from decimal import Decimal

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


class StripeService:
    """Service class wrapping Stripe API operations."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        booking,
        payment_method_id: str = None,
    ) -> dict:
        """
        Create a Stripe Payment Intent for a booking.

        Returns:
            dict with payment_intent_id and client_secret
        """
        # Convert amount to cents
        amount_cents = int(amount * 100)

        intent_params = {
            "amount": amount_cents,
            "currency": currency.lower(),
            "metadata": {
                "booking_id": str(booking.id),
                "booking_reference": booking.reference,
                "host_email": booking.host.email,
                "invitee_email": booking.invitee_email,
            },
            "receipt_email": booking.invitee_email,
            "description": f"Booking {booking.reference}",
        }

        if payment_method_id:
            intent_params["payment_method"] = payment_method_id
            intent_params["confirm"] = True

        # If host has a connected Stripe account, use it for direct charges
        if hasattr(booking.host, "payout_account"):
            payout_account = booking.host.payout_account
            if payout_account.charges_enabled and payout_account.stripe_account_id:
                platform_fee_cents = int(amount_cents * 0.029)
                intent_params["transfer_data"] = {
                    "destination": payout_account.stripe_account_id,
                }
                intent_params["application_fee_amount"] = platform_fee_cents

        intent = stripe.PaymentIntent.create(**intent_params)

        logger.info(
            "Created Payment Intent %s for booking %s",
            intent.id,
            booking.reference,
        )

        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "status": intent.status,
        }

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Decimal = None,
    ) -> dict:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: Stripe Payment Intent ID
            amount: Refund amount (None for full refund)

        Returns:
            dict with refund_id and status
        """
        refund_params = {
            "payment_intent": payment_intent_id,
        }

        if amount is not None:
            refund_params["amount"] = int(amount * 100)

        refund = stripe.Refund.create(**refund_params)

        logger.info("Created refund %s for intent %s", refund.id, payment_intent_id)

        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount / 100,
        }

    def create_connect_account(self, user) -> dict:
        """
        Create a Stripe Connect Express account for a user.

        Returns:
            dict with account_id and onboarding_url
        """
        account = stripe.Account.create(
            type="express",
            email=user.email,
            metadata={
                "user_id": str(user.id),
            },
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )

        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{settings.FRONTEND_URL}/settings/payments?refresh=true",
            return_url=f"{settings.FRONTEND_URL}/settings/payments?success=true",
            type="account_onboarding",
        )

        logger.info("Created Connect account %s for user %s", account.id, user.email)

        return {
            "account_id": account.id,
            "onboarding_url": account_link.url,
        }

    def get_account_balance(self, stripe_account_id: str) -> dict:
        """Get balance for a connected Stripe account."""
        balance = stripe.Balance.retrieve(
            stripe_account=stripe_account_id,
        )

        available = sum(
            b["amount"] for b in balance.get("available", [])
        ) / 100

        pending = sum(
            b["amount"] for b in balance.get("pending", [])
        ) / 100

        return {
            "available": available,
            "pending": pending,
            "currency": balance["available"][0]["currency"] if balance.get("available") else "usd",
        }
