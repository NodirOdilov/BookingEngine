"""
URL configuration for payments app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentViewSet,
    PayoutAccountView,
    RefundViewSet,
    stripe_webhook,
)

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"refunds", RefundViewSet, basename="refund")

urlpatterns = [
    path("payout-account/", PayoutAccountView.as_view(), name="payout-account"),
    path("webhook/stripe/", stripe_webhook, name="stripe-webhook"),
    path("", include(router.urls)),
]
