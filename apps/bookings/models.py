import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.providers.models import Provider
from apps.services.models import Service


def _default_held_until():
    """12-hour hold window from creation time."""
    return timezone.now() + timedelta(hours=12)


class AppointmentRequest(models.Model):
    """
    The operational hub of the salon's appointment system.

    Clients submit a consultation request with hair photos and deposit proof.
    An admin manually reviews suitability and approves/rejects.
    This is NOT an instant booking system.
    """

    class Status(models.TextChoices):
        PENDING_VERIFICATION = "pending_verification", "Pending Verification"
        PENDING_REVIEW = "pending_review", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    class HairLength(models.TextChoices):
        EAR = "ear", "Ear Length"
        CHIN = "chin", "Chin Length"
        NECK = "neck", "Neck Length"
        SHOULDER = "shoulder", "Shoulder Length"
        ARMPIT = "armpit", "Armpit Length"
        BRA_STRAP = "bra_strap", "Bra Strap Length"
        MID_BACK = "mid_back", "Mid Back Length"
        WAIST = "waist", "Waist Length"
        HIP = "hip", "Hip Length"

    class PaymentMethod(models.TextChoices):
        REVOLUT = "revolut", "Revolut"
        WISE = "wise", "Wise"
        TRANSFERGO = "transfergo", "TransferGo"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"

    class PaymentStatus(models.TextChoices):
        PENDING_VERIFICATION = "pending_verification", "Pending Verification"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    # ── Relations ──────────────────────────────────────────────
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        related_name="appointment_requests",
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE,
        related_name="appointment_requests",
    )
    selected_options = models.JSONField(
        default=dict, blank=True,
        help_text="Frozen historical snapshot of selected option IDs and values.",
    )

    # ── Client Data (no accounts — zero friction) ──────────────
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=30)
    client_age = models.PositiveSmallIntegerField(
        help_text="Client's age. Validated against service target_audience."
    )

    # ── Hair Data ──────────────────────────────────────────────
    hair_length = models.CharField(max_length=20, choices=HairLength.choices)
    photo_front = models.ImageField(upload_to="hair_photos/")
    photo_side = models.ImageField(upload_to="hair_photos/")
    photo_back = models.ImageField(upload_to="hair_photos/")

    # ── Financials ─────────────────────────────────────────────
    deposit_amount = models.PositiveIntegerField(
        help_text="Calculated deposit amount in HUF (frozen at request time)."
    )
    payment_method = models.CharField(
        max_length=30, choices=PaymentMethod.choices, blank=True
    )
    payment_reference = models.CharField(
        max_length=20, unique=True, blank=True,
        help_text="Auto-generated. Format: AFH-XXXXXX"
    )
    proof_of_payment = models.ImageField(
        upload_to="payment_proofs/", blank=True,
        help_text="Screenshot of the manual bank transfer.",
    )

    # ── Payment Verification ───────────────────────────────────
    payment_status = models.CharField(
        max_length=30, choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING_VERIFICATION,
    )

    # ── Timers & State ─────────────────────────────────────────
    target_date = models.DateField()
    target_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    held_until = models.DateTimeField(
        default=_default_held_until,
        help_text="Slot is held until this time. Auto-expires if admin doesn't act."
    )
    status = models.CharField(
        max_length=30, choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )
    # Reminder tracking — set True once each reminder email has been sent,
    # so the reminder command is idempotent across cron runs.
    reminder_2h_sent = models.BooleanField(
        default=False,
        help_text="Set True once the 2-hour-before-expiry reminder email has been sent.",
    )
    reminder_1h_sent = models.BooleanField(
        default=False,
        help_text="Set True once the 1-hour-before-expiry reminder email has been sent.",
    )

    # ── Admin Notes ────────────────────────────────────────────
    admin_notes = models.TextField(
        blank=True,
        help_text="Notes visible to the client on the Guest Lookup page."
    )
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes — NOT shown to clients."
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Appointment Request"
        verbose_name_plural = "Appointment Requests"

    def __str__(self):
        return f"{self.payment_reference} — {self.client_name} — {self.service.title}"

    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"AFH-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    # ── Convenience Properties ─────────────────────────────────
    @property
    def is_held(self):
        """True if the request is still within its hold window."""
        return self.held_until > timezone.now() and self.status in (
            self.Status.PENDING_VERIFICATION,
            self.Status.PENDING_REVIEW,
        )


class RefundQueueManager(models.Manager):
    """Manager that filters to only rejected/expired requests."""

    def get_queryset(self):
        return super().get_queryset().filter(
            status__in=[
                AppointmentRequest.Status.REJECTED,
                AppointmentRequest.Status.EXPIRED,
            ]
        )


class RefundQueue(AppointmentRequest):
    """
    Proxy model of AppointmentRequest, filtered to rejected/expired statuses.
    Used by admins to track who needs a manual bank-transfer refund.
    """

    objects = RefundQueueManager()

    class Meta:
        proxy = True
        verbose_name = "Refund Queue Item"
        verbose_name_plural = "Refund Queue"
        ordering = ["-created_at"]
