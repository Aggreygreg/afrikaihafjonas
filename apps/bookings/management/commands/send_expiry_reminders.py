from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import AppointmentRequest
from apps.site_config.models import SiteConfiguration


# Request statuses that are still "live" — waiting on admin action.
ACTIVE_STATUSES = (
    AppointmentRequest.Status.PENDING_VERIFICATION,
    AppointmentRequest.Status.PENDING_REVIEW,
)

# Reminder windows evaluated in order: (hours before expiry, boolean flag field).
# The 2h window is evaluated first; once its flag is set it won't re-fire, so a
# request that later enters the 1h window only triggers the 1h reminder.
REMINDER_WINDOWS = (
    (2, "reminder_2h_sent"),
    (1, "reminder_1h_sent"),
)


def get_admin_email():
    """
    Recipient address for reminder emails.

    Prefers the salon email configured in the SiteConfiguration singleton,
    falling back to Django's DEFAULT_FROM_EMAIL when it is blank/unavailable.
    """
    salon_email = ""
    try:
        salon_email = (SiteConfiguration.get_solo().salon_email or "").strip()
    except Exception:
        # SiteConfiguration table not ready / app not installed — stay safe.
        salon_email = ""
    return salon_email or settings.DEFAULT_FROM_EMAIL


def get_admin_change_url(req):
    """Path to the admin review page for a single appointment request."""
    try:
        return reverse("admin:bookings_appointmentrequest_change", args=[req.pk])
    except Exception:
        # Fallback if the admin URL config isn't resolvable for any reason.
        return f"/admin/bookings/appointmentrequest/{req.pk}/change/"


class Command(BaseCommand):
    help = (
        "Sends expiry reminder emails to the salon admin for active appointment "
        "requests within 2h / 1h of their hold deadline. Idempotent: each "
        "reminder is sent at most once per request. Run via cron every 15-30 min."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without sending emails or updating flags.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options["dry_run"]
        recipient = get_admin_email()

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No emails will be sent."))

        total_sent = 0

        for hours, flag_field in REMINDER_WINDOWS:
            window_start = now + timedelta(hours=hours)
            qs = (
                AppointmentRequest.objects.filter(
                    status__in=ACTIVE_STATUSES,
                    held_until__lte=window_start,  # within `hours` of expiry...
                    held_until__gt=now,           # ...but not yet expired
                    **{flag_field: False},
                )
                .select_related("service", "provider")
                .order_by("held_until")
            )

            for req in qs:
                subject = (
                    f"[Afrikai Hajfonás] ⏰ {hours}h until expiry: "
                    f"{req.payment_reference}"
                )
                context = {
                    "hours": hours,
                    "reference": req.payment_reference,
                    "client_name": req.client_name,
                    "service_title": req.service.title,
                    "provider_name": req.provider.display_name,
                    "target_date": req.target_date,
                    "target_time": req.target_time,
                    "status": req.get_status_display(),
                    "held_until": timezone.localtime(req.held_until),
                    "admin_url": get_admin_change_url(req),
                }
                body = render_to_string(
                    "bookings/emails/expiry_reminder.txt", context
                )

                if dry_run:
                    self.stdout.write(
                        f"  [{hours}h] {req.payment_reference} — "
                        f"{req.client_name} (held_until="
                        f"{context['held_until']:%Y-%m-%d %H:%M}) -> {recipient}"
                    )
                    continue

                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )

                setattr(req, flag_field, True)
                req.save(update_fields=[flag_field])
                total_sent += 1

                self.stdout.write(
                    f"  Sent {hours}h reminder for {req.payment_reference} "
                    f"({req.client_name}) -> {recipient}"
                )

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Done (nothing was sent)."))
        elif total_sent:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent {total_sent} expiry reminder email(s) to {recipient}."
                )
            )
        else:
            self.stdout.write("No expiry reminders due.")

        return f"{total_sent} reminder(s) sent"
