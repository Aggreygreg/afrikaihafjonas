from django.contrib import admin

from .models import AppointmentRequest, RefundQueue


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "payment_reference",
        "client_name",
        "service",
        "provider",
        "target_date",
        "target_time",
        "status",
        "payment_status",
        "held_until",
    )
    list_filter = ("status", "payment_status", "provider", "target_date")
    search_fields = (
        "payment_reference",
        "client_name",
        "client_email",
        "client_phone",
    )
    readonly_fields = (
        "payment_reference",
        "created_at",
        "held_until",
        "selected_options",
    )
    date_hierarchy = "target_date"
    ordering = ("-created_at",)


@admin.register(RefundQueue)
class RefundQueueAdmin(admin.ModelAdmin):
    """
    Admin view filtered to only rejected/expired requests.
    Used by salon owner to track who needs a manual bank-transfer refund.
    """
    list_display = (
        "payment_reference",
        "client_name",
        "client_email",
        "service",
        "deposit_amount",
        "payment_method",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_method")
    search_fields = (
        "payment_reference",
        "client_name",
        "client_email",
    )
    readonly_fields = (
        "payment_reference",
        "created_at",
        "held_until",
    )
    ordering = ("-created_at",)
