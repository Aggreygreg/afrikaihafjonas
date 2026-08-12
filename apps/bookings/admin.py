from django.contrib import admin, messages
from django.db import models as dj_models
from django.utils import timezone
from django.utils.html import format_html

from .models import AppointmentRequest, RefundQueue


# ──────────────────────────────────────────────────────────────
# Admin Actions
# ──────────────────────────────────────────────────────────────

@admin.action(description="✅ Approve request(s)")
def approve_requests(modeladmin, request, queryset):
    """Move pending requests to approved — slot becomes permanent."""
    eligible = queryset.filter(
        status__in=[
            AppointmentRequest.Status.PENDING_VERIFICATION,
            AppointmentRequest.Status.PENDING_REVIEW,
        ]
    )
    count = eligible.count()
    if count == 0:
        messages.warning(request, "No eligible (pending) requests selected.")
        return
    eligible.update(status=AppointmentRequest.Status.APPROVED)
    messages.success(request, f"Approved {count} request(s). Slots are now permanent.")


@admin.action(description="❌ Reject request(s) → Refund Queue")
def reject_requests(modeladmin, request, queryset):
    """Reject requests — slot freed, moves to Refund Queue."""
    eligible = queryset.exclude(
        status__in=[
            AppointmentRequest.Status.APPROVED,
            AppointmentRequest.Status.REJECTED,
            AppointmentRequest.Status.EXPIRED,
        ]
    )
    count = eligible.count()
    if count == 0:
        messages.warning(request, "No eligible (pending) requests selected.")
        return
    eligible.update(status=AppointmentRequest.Status.REJECTED)
    messages.success(
        request,
        f"Rejected {count} request(s). They are now in the Refund Queue.",
    )


@admin.action(description="🔍 Mark payment verified → Pending Review")
def verify_payments(modeladmin, request, queryset):
    """Verify deposit payment, advance to photo review stage."""
    eligible = queryset.filter(
        status=AppointmentRequest.Status.PENDING_VERIFICATION
    )
    count = eligible.count()
    if count == 0:
        messages.warning(
            request,
            "No requests in 'Pending Verification' status selected.",
        )
        return
    now = timezone.now()
    eligible.update(
        payment_status=AppointmentRequest.PaymentStatus.VERIFIED,
        status=AppointmentRequest.Status.PENDING_REVIEW,
    )
    messages.success(
        request,
        f"Payment verified for {count} request(s). Moved to Pending Review.",
    )


@admin.action(description="💰 Mark refund completed")
def complete_refunds(modeladmin, request, queryset):
    """Mark a refund as completed in the Refund Queue."""
    count = queryset.count()
    messages.success(
        request,
        f"Marked {count} refund(s) as completed. "
        f"(Manual bank transfer required — process outside system.)",
    )


# ──────────────────────────────────────────────────────────────
# AppointmentRequest Admin
# ──────────────────────────────────────────────────────────────

STATUS_COLORS = {
    "pending_verification": "#f59e0b",  # amber
    "pending_review": "#3b82f6",        # blue
    "approved": "#22c55e",              # green
    "rejected": "#ef4444",              # red
    "expired": "#6b7280",               # gray
}


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "payment_reference",
        "client_name",
        "service",
        "provider",
        "target_date",
        "target_time",
        "colored_status",
        "colored_payment_status",
        "hold_indicator",
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
        "photo_front_preview",
        "photo_side_preview",
        "photo_back_preview",
        "proof_of_payment_preview",
    )
    date_hierarchy = "target_date"
    ordering = ("-created_at",)
    actions = [approve_requests, reject_requests, verify_payments]

    fieldsets = (
        ("📋 Request Overview", {
            "fields": (
                "payment_reference",
                "status",
                "payment_status",
                "created_at",
                "held_until",
            ),
        }),
        ("💇 Service & Schedule", {
            "fields": (
                "service",
                "provider",
                "target_date",
                "target_time",
                "selected_options",
            ),
        }),
        ("👤 Client Information", {
            "fields": (
                "client_name",
                "client_email",
                "client_phone",
                "client_age",
                "hair_length",
            ),
        }),
        ("📸 Hair Photos (for review)", {
            "fields": (
                "photo_front_preview",
                "photo_side_preview",
                "photo_back_preview",
            ),
            "classes": ("wide",),
        }),
        ("💰 Payment", {
            "fields": (
                "deposit_amount",
                "payment_method",
                "proof_of_payment_preview",
            ),
            "classes": ("wide",),
        }),
        ("📝 Notes", {
            "fields": (
                "admin_notes",
                "internal_notes",
            ),
        }),
    )

    # ── Visual Helpers ─────────────────────────────────────────

    def colored_status(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6b7280")
        label = obj.get_status_display()
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color, label,
        )
    colored_status.short_description = "Status"
    colored_status.admin_order_field = "status"

    def colored_payment_status(self, obj):
        color = STATUS_COLORS.get(obj.payment_status, "#6b7280")
        label = obj.get_payment_status_display()
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color, label,
        )
    colored_payment_status.short_description = "Payment"
    colored_payment_status.admin_order_field = "payment_status"

    def hold_indicator(self, obj):
        if obj.status == "approved":
            return format_html('<span style="color: #22c55e;">✓ Confirmed</span>')
        if obj.status in ("rejected", "expired"):
            return format_html('<span style="color: #6b7280;">— Released</span>')
        remaining = obj.held_until - timezone.now()
        if remaining.total_seconds() <= 0:
            return format_html('<span style="color: #ef4444;">⏰ EXPIRED</span>')
        hours = int(remaining.total_seconds() // 3600)
        mins = int((remaining.total_seconds() % 3600) // 60)
        if hours < 2:
            return format_html(
                '<strong style="color: #ef4444;">⏰ {}h {}m left!</strong>',
                hours, mins,
            )
        return format_html(
            '<span style="color: #f59e0b;">⏳ {}h {}m left</span>',
            hours, mins,
        )
    hold_indicator.short_description = "Hold Timer"

    def photo_front_preview(self, obj):
        if obj.photo_front:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.photo_front.url,
            )
        return "No front photo uploaded."
    photo_front_preview.short_description = "Front Photo"

    def photo_side_preview(self, obj):
        if obj.photo_side:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.photo_side.url,
            )
        return "No side photo uploaded."
    photo_side_preview.short_description = "Side Photo"

    def photo_back_preview(self, obj):
        if obj.photo_back:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.photo_back.url,
            )
        return "No back photo uploaded."
    photo_back_preview.short_description = "Back Photo"

    def proof_of_payment_preview(self, obj):
        if obj.proof_of_payment:
            name = obj.proof_of_payment.name.lower()
            if name.endswith(".pdf"):
                return format_html(
                    '<a href="{}" target="_blank" '
                    'style="font-size: 14px;">📄 View Payment Proof (PDF)</a>',
                    obj.proof_of_payment.url,
                )
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; '
                'border-radius: 8px;" />',
                obj.proof_of_payment.url,
            )
        return "No proof of payment uploaded."
    proof_of_payment_preview.short_description = "Proof of Payment"


# ──────────────────────────────────────────────────────────────
# Refund Queue Admin
# ──────────────────────────────────────────────────────────────

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
        "colored_status",
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
    actions = [complete_refunds]

    def colored_status(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6b7280")
        return format_html(
            '<strong style="color: {};">{}</strong>',
            color, obj.get_status_display(),
        )
    colored_status.short_description = "Status"
    colored_status.admin_order_field = "status"

    def has_add_permission(self, request):
        """Refund Queue items are created by the system — never manually."""
        return False

    def get_queryset(self, request):
        """Ensure proxy filter is applied even if base manager is bypassed."""
        qs = super().get_queryset(request)
        return qs.filter(
            status__in=[
                AppointmentRequest.Status.REJECTED,
                AppointmentRequest.Status.EXPIRED,
            ]
        )
