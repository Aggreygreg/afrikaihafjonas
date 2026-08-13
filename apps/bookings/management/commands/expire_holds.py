from datetime import timedelta

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import AppointmentRequest


class Command(BaseCommand):
    help = (
        "Auto-expires appointment requests whose 12-hour hold window "
        "has elapsed without admin action. Run via cron every 15-30 minutes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without writing to the database.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options["dry_run"]

        # Requests still pending but past their hold deadline
        expired_qs = AppointmentRequest.objects.filter(
            status__in=[
                AppointmentRequest.Status.PENDING_VERIFICATION,
                AppointmentRequest.Status.PENDING_REVIEW,
            ],
            held_until__lt=now,
        )

        count = expired_qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {count} request(s) would be expired."
                )
            )
            for req in expired_qs:
                self.stdout.write(f"  {req.payment_reference} — {req.client_name}")
            return

        if count == 0:
            self.stdout.write("No expired holds to process.")
            return

        expired_refs = []
        for req in expired_qs:
            req.status = AppointmentRequest.Status.EXPIRED
            req.save(update_fields=["status"])
            expired_refs.append(req.payment_reference)

            # Send customer-facing 'appointment_expired' email.
            # Uses appointment.customer_language for language selection.
            from apps.bookings.notifications import send_appointment_email
            send_appointment_email(req, "appointment_expired")

        # Notify admin
        refs_text = "\n".join(expired_refs)
        mail_admins(
            subject=f"[Afrikai Hajfonás] {count} appointment request(s) auto-expired",
            message=(
                f"The following {count} request(s) have been automatically "
                f"expired because their 12-hour hold window elapsed without "
                f"admin action:\n\n{refs_text}\n\n"
                f"These customers should receive a refund (see Refund Queue)."
            ),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count} request(s): {', '.join(expired_refs)}"
            )
        )
