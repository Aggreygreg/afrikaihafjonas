import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import get_language, gettext_lazy as _

from apps.providers.models import Provider
from apps.services.models import Service
from apps.site_config.constants import LanguageChoices


def _active_lang():
    """Return the current 2-letter language code, defaulting to HU (base)."""
    lang = get_language() or LanguageChoices.HU
    return lang[:2]


def _default_held_until():
    """12-hour hold window from creation time."""
    return timezone.now() + timedelta(hours=12)


# ── Payment Configuration Models ───────────────────────────────

class PaymentMethod(models.Model):
    """Admin-managed payment method. Admin can add, edit, disable, reorder.

    These are SEED DATA, not architectural constants. The four initial methods
    (Revolut, Wise, TransferGo, Bank Transfer) are seeded at migration time.
    The admin may delete them and create entirely different ones.

    Decision #38: ``name`` is in PaymentMethodTranslation (HU/EN/DE).
    """
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    icon = models.ImageField(upload_to='payment_icons/', blank=True, null=True)

    class Meta:
        ordering = ['display_order', 'pk']

    def __str__(self):
        trans = self.translations.filter(language=LanguageChoices.HU).first()
        return trans.name if trans else f"Payment Method #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            trans = self.translations.filter(language=LanguageChoices.HU).first()
            base = trans.name if trans else f"payment-method-{self.pk or 'new'}"
            self.slug = slugify(base)
        super().save(*args, **kwargs)

    def get_translation(self, lang=None):
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    @property
    def display_name(self):
        trans = self.get_translation()
        return trans.name if trans else str(self)


class PaymentDetailField(models.Model):
    """Admin-defined field for a payment method (IBAN, account holder, QR code, etc.).

    This is the CURRENT configuration. When an appointment is created,
    these values are SNAPSHOTTED into the appointment's payment snapshot.
    Editing this record later does NOT change historical appointments.
    """
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('image', 'Image'),
    ]

    payment_method = models.ForeignKey(
        PaymentMethod, related_name='detail_fields', on_delete=models.CASCADE
    )
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    value = models.TextField(blank=True)
    image_value = models.ImageField(
        upload_to='payment_details/', blank=True, null=True,
        help_text="For image type fields (e.g., QR codes)."
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        trans = self.translations.filter(language=LanguageChoices.HU).first()
        label = trans.label if trans else f"Field #{self.pk}"
        return f"{self.payment_method} — {label}"

    def get_translation(self, lang=None):
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    @property
    def display_label(self):
        trans = self.get_translation()
        return trans.label if trans else str(self)


class AppointmentPaymentSnapshot(models.Model):
    """Frozen copy of the payment configuration at the time of appointment submission.

    Created when the customer selects a payment method and submits (Step 4).
    NEVER updated after creation.

    VISIBILITY:
      - payment_method_name: used by Guest Lookup (customer-visible, read-only)
      - detail_fields_snapshot: ADMIN-ONLY audit record. NEVER shown to customers.
        Per Decision #15, bank transfer details are always hidden from clients.

    Image-type detail fields are physically copied to payment_snapshots/<ref>/
    at snapshot creation time.
    """
    appointment = models.OneToOneField(
        'bookings.AppointmentRequest',
        related_name='payment_snapshot',
        on_delete=models.CASCADE,
    )
    payment_method_name = models.CharField(max_length=100)
    payment_method_slug = models.SlugField(max_length=100, blank=True)
    detail_fields_snapshot = models.JSONField(default=list)
    snapshot_created_at = models.DateTimeField(auto_now_add=True)

    def get_detail(self, label):
        """Retrieve a frozen detail value by label."""
        for field in self.detail_fields_snapshot:
            if field['label'] == label:
                return field['value']
        return None

    def __str__(self):
        return f"Payment Snapshot — {self.payment_method_name}"


# ── Appointment Request ────────────────────────────────────────

class AppointmentRequest(models.Model):
    """
    The operational hub of the salon's appointment system.

    Clients submit a consultation request with hair photos and deposit proof.
    An admin manually reviews suitability and approves/rejects.
    This is NOT an instant booking system.
    """

    class Status(models.TextChoices):
        PENDING_VERIFICATION = "pending_verification", _("Pending Verification")
        PENDING_REVIEW = "pending_review", _("Pending Review")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        EXPIRED = "expired", _("Expired")

    class HairLength(models.TextChoices):
        EAR = "ear", _("Ear")
        CHIN = "chin", _("Chin")
        NECK = "neck", _("Neck")
        SHOULDER = "shoulder", _("Shoulder")
        ARMPIT = "armpit", _("Armpit")
        BRA_STRAP = "bra_strap", _("Bra Strap")
        MID_BACK = "mid_back", _("Mid Back")
        WAIST = "waist", _("Waist")
        HIP = "hip", _("Hip")

    # Legacy TextChoices — KEPT for data migration reference only.
    # The actual field has been replaced by payment_method_fk.
    _LEGACY_PAYMENT_CHOICES = [
        ("revolut", "Revolut"),
        ("wise", "Wise"),
        ("transfergo", "TransferGo"),
        ("bank_transfer", "Bank Transfer"),
    ]

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
    payment_method_fk = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="appointments",
        help_text="FK to live PaymentMethod for admin querying. "
                  "Historical detail is in the payment_snapshot.",
    )
    payment_reference = models.CharField(
        max_length=20, unique=True, blank=True,
        help_text="Auto-generated. Format: AFH-XXXXXX"
    )
    proof_of_payment = models.ImageField(
        upload_to="payment_proofs/", blank=True,
        help_text="Screenshot of the manual bank transfer.",
    )

    # ── Language Persistence (Decision #28) ────────────────────
    customer_language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.HU,
        help_text="Captured at submission. Immutable. Drives all appointment emails."
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
        return f"{self.payment_reference} — {self.client_name} — {self.service.display_title}"

    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"AFH-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_held(self):
        """True if the slot is still within the hold window."""
        return timezone.now() < self.held_until and self.status in (
            self.Status.PENDING_VERIFICATION,
            self.Status.PENDING_REVIEW,
        )

    # ── Snapshot Helpers ───────────────────────────────────────

    def create_payment_snapshot(self, payment_method=None):
        """Create or replace the payment snapshot for this appointment.

        Copies image-type PaymentDetailField files to payment_snapshots/<ref>/
        to guarantee the audit record survives later file deletion.

        Args:
            payment_method: PaymentMethod instance to snapshot.
                            Defaults to self.payment_method_fk.
        """
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        import os

        pm = payment_method or self.payment_method_fk
        if pm is None:
            return None

        detail_snapshot = []
        ref = self.payment_reference or str(self.pk)

        for field in pm.detail_fields.filter(is_active=True).order_by('display_order'):
            entry = {
                'label': field.display_label,
                'field_type': field.field_type,
                'value': '',
            }
            if field.field_type == 'image' and field.image_value:
                # Physical copy to immutable path
                src_path = field.image_value.path
                if os.path.exists(src_path):
                    ext = os.path.splitext(src_path)[1]
                    new_name = f"{slugify(field.display_label)}{ext}"
                    dest_path = f"payment_snapshots/{ref}/{new_name}"
                    with open(src_path, 'rb') as f:
                        saved_path = default_storage.save(dest_path, ContentFile(f.read()))
                    entry['value'] = saved_path
            else:
                entry['value'] = field.value or ''
            detail_snapshot.append(entry)

        snapshot, created = AppointmentPaymentSnapshot.objects.update_or_create(
            appointment=self,
            defaults={
                'payment_method_name': pm.display_name,
                'payment_method_slug': pm.slug,
                'detail_fields_snapshot': detail_snapshot,
            },
        )
        return snapshot


# ── Refund Queue (proxy) ────────────────────────────────────────

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


# ── Payment Translation Models (Category B) ───────────────────
# Decision #38: Full customer-facing multilingual support (HU/EN/DE).
# Payment method names and field labels are customer-visible and must
# be translated. PaymentDetailField.value is operational data (IBAN,
# account numbers) and is NOT translated.

class PaymentMethodTranslation(models.Model):
    """One translation per language for a PaymentMethod."""

    payment_method = models.ForeignKey(
        PaymentMethod, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('payment_method', 'language')
        verbose_name = "Payment method translation"
        verbose_name_plural = "Payment method translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.name}"


class PaymentDetailFieldTranslation(models.Model):
    """One translation per language for a PaymentDetailField label."""

    payment_detail_field = models.ForeignKey(
        PaymentDetailField, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    label = models.CharField(max_length=100)

    class Meta:
        unique_together = ('payment_detail_field', 'language')
        verbose_name = "Payment detail field translation"
        verbose_name_plural = "Payment detail field translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.label}"
