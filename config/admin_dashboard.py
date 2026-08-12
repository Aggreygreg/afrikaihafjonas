"""
Patches Django's AdminSite.index to render a custom dashboard with
operational statistics (pending verifications, review queue, today's
schedule, refund queue, revenue metrics).

Import this module from config/urls.py — it runs once at startup.
"""
from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.utils import timezone

# Tell Django to use our custom index template
AdminSite.index_template = "admin/index.html"

# Save the original index method
_original_index = AdminSite.index


def _build_dashboard_context(request):
    """Compute operational statistics for the admin dashboard."""
    from apps.bookings.models import AppointmentRequest

    now = timezone.now()
    today = now.date()
    two_hours_from_now = now + timedelta(hours=2)

    Status = AppointmentRequest.Status

    pending_verification = AppointmentRequest.objects.filter(
        status=Status.PENDING_VERIFICATION
    ).select_related("service", "provider")

    pending_review = AppointmentRequest.objects.filter(
        status=Status.PENDING_REVIEW
    ).select_related("service", "provider")

    # Expiring soon: pending requests whose hold ends within 2 hours
    expiring_soon_qs = AppointmentRequest.objects.filter(
        status__in=[Status.PENDING_VERIFICATION, Status.PENDING_REVIEW],
        held_until__lte=two_hours_from_now,
        held_until__gt=now,
    ).select_related("service", "provider").order_by("held_until")

    # Today's confirmed appointments
    today_appointments = AppointmentRequest.objects.filter(
        status=Status.APPROVED,
        target_date=today,
    ).select_related("service", "provider").order_by("target_time")

    # Refund queue
    refund_qs = AppointmentRequest.objects.filter(
        status__in=[Status.REJECTED, Status.EXPIRED],
    )

    # Approved requests (all time)
    approved_qs = AppointmentRequest.objects.filter(status=Status.APPROVED)

    # Total approved deposit revenue
    from django.db.models import Sum

    total_deposits = approved_qs.aggregate(
        total=Sum("deposit_amount")
    )["total"] or 0

    # Build "expires in" human strings for the urgent table
    expiring_list = []
    for req in expiring_soon_qs[:10]:
        remaining = req.held_until - now
        hours = int(remaining.total_seconds() // 3600)
        mins = int((remaining.total_seconds() % 3600) // 60)
        req.expires_in = f"{hours}h {mins}m"
        expiring_list.append(req)

    # Pending action queue (most recent, across verification + review)
    pending_queue = list(pending_verification[:5]) + list(pending_review[:5])

    return {
        # Widget counts
        "pending_verification_count": pending_verification.count(),
        "pending_review_count": pending_review.count(),
        "expiring_soon_count": expiring_soon_qs.count(),
        "today_confirmed_count": today_appointments.count(),
        "refund_queue_count": refund_qs.count(),
        "approved_count": approved_qs.count(),
        "total_approved_deposits": f"{total_deposits:,} Ft",
        # Tables
        "expiring_soon": expiring_list,
        "today_appointments": today_appointments[:15],
        "pending_queue": pending_queue,
        # Today's date parts for filtered links
        "today_year": today.year,
        "today_month": today.month,
        "today_day": today.day,
    }


def dashboard_index(self, request, extra_context=None):
    """Custom admin index with dashboard widgets."""
    extra_context = extra_context or {}
    extra_context.update(_build_dashboard_context(request))
    return _original_index(self, request, extra_context)


# Patch at the class level so self is passed correctly
AdminSite.index = dashboard_index
