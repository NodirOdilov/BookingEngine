"""
Admin configuration for payments app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Payment, PayoutAccount, Refund


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ["refunded_at", "created_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id_short",
        "booking_ref",
        "payer_email",
        "amount",
        "currency",
        "status_badge",
        "payment_method_type",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "payment_method_type", "currency"]
    search_fields = [
        "payer_email",
        "payer_name",
        "booking__reference",
        "stripe_payment_intent_id",
    ]
    readonly_fields = [
        "stripe_payment_intent_id",
        "stripe_charge_id",
        "paid_at",
        "created_at",
        "updated_at",
    ]
    inlines = [RefundInline]

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = "ID"

    def booking_ref(self, obj):
        return obj.booking.reference
    booking_ref.short_description = "Booking"

    def status_badge(self, obj):
        colors = {
            "pending": "#F59E0B",
            "processing": "#3B82F6",
            "completed": "#10B981",
            "failed": "#EF4444",
            "refunded": "#8B5CF6",
            "cancelled": "#6B7280",
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="padding:3px 8px;border-radius:4px;background:{};color:white;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"


@admin.register(PayoutAccount)
class PayoutAccountAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "stripe_account_id",
        "account_status",
        "charges_enabled",
        "payouts_enabled",
        "total_earned",
        "total_paid_out",
    ]
    list_filter = ["account_status", "charges_enabled", "payouts_enabled"]
    search_fields = ["user__email", "stripe_account_id"]
    readonly_fields = ["created_at", "updated_at"]
