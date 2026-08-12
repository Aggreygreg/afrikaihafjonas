"""
Consultation wizard forms — Steps 3 & 4.

Step 3 (WizardStep3Form): client details, hair length, three hair photos and
    GDPR consent. Age is validated against the service's ``target_audience``.
Step 4 (WizardStep4Form): payment method, proof-of-payment upload and final
    consent. The proof field accepts PDF in addition to images, so it is
    declared as a plain ``FileField`` (the model ``ImageField`` would reject
    PDFs via Pillow).
"""

import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import AppointmentRequest, PaymentMethod


# ── Upload validation constants ──────────────────────────────
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

HAIR_PHOTO_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
PROOF_EXTENSIONS = [".jpg", ".jpeg", ".png", ".pdf"]

HAIR_PHOTO_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]
PROOF_CONTENT_TYPES = ["image/jpeg", "image/png", "application/pdf"]


# ── Shared widget styling ────────────────────────────────────
_TEXT_INPUT_CLASS = (
    "w-full p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm "
    "focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
)
_FILE_INPUT_CLASS = (
    "block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-4 "
    "file:rounded-lg file:border-0 file:text-sm file:font-semibold "
    "file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
)


# ── Age validation (source of truth: MASTER_CONTEXT §4) ──────
def get_age_validation_error(age, target_audience):
    """
    Return a translated error message if ``age`` violates the policy for the
    given ``target_audience``, otherwise ``None``.

    Rules:
      - Adults (16+)    -> minimum age 16
      - Children (8-15) -> age must be between 8 and 15
      - Everyone (8+)   -> minimum age 8
      - Under 8         -> always blocked (covered by the above minimums)
    """
    if target_audience == "Adults":
        if age < 16:
            return _("This service is for adults aged 16 and over.")
    elif target_audience == "Children":
        if age < 8 or age > 15:
            return _("This service is for children aged 8 to 15.")
    else:  # "Everyone" (or any future value) -> minimum age 8
        if age < 8:
            return _("Clients must be at least 8 years old for this service.")
    return None


def _validate_upload(upload, allowed_extensions, allowed_content_types, label):
    """Shared size + type validation for an uploaded file."""
    if not upload:
        return upload

    if upload.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            _("%(label)s is too large. The maximum file size is 5 MB."),
            params={"label": label},
        )

    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _("%(label)s has an unsupported format. Allowed: %(formats)s."),
            params={"label": label, "formats": ", ".join(allowed_extensions)},
        )

    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in allowed_content_types:
        raise ValidationError(
            _("%(label)s has an unsupported file type."),
            params={"label": label},
        )

    return upload


class WizardStep3Form(forms.ModelForm):
    """Step 3 — Client details, hair data, photos and GDPR consent."""

    gdpr_consent = forms.BooleanField(
        required=True,
        label=_(
            "I have read and accept the Privacy Policy and consent to the "
            "processing of my personal data and hair photos for this "
            "consultation request."
        ),
        error_messages={
            "required": _("You must accept the privacy policy to continue."),
        },
    )

    class Meta:
        model = AppointmentRequest
        fields = [
            "client_name",
            "client_email",
            "client_phone",
            "client_age",
            "hair_length",
            "photo_front",
            "photo_side",
            "photo_back",
        ]

    def __init__(self, *args, target_audience="Adults", **kwargs):
        super().__init__(*args, **kwargs)
        # Needed for server-side age enforcement in clean_client_age().
        self.target_audience = target_audience

        # Remove any auto-added blank choice so the template's choice loop
        # doesn't render a stray '---------' radio card.
        self.fields["hair_length"].choices = AppointmentRequest.HairLength.choices

        hair_accept = "image/jpeg,image/png,image/webp"
        for field_name in ("photo_front", "photo_side", "photo_back"):
            self.fields[field_name].widget.attrs.update(
                {"accept": hair_accept, "class": _FILE_INPUT_CLASS}
            )
            self.fields[field_name].help_text = _(
                "JPG, PNG or WEBP — max 5 MB."
            )

        for field_name in ("client_name", "client_email", "client_phone"):
            self.fields[field_name].widget.attrs.update({"class": _TEXT_INPUT_CLASS})

        self.fields["client_age"].widget.attrs.update(
            {
                "class": _TEXT_INPUT_CLASS,
                "min": 8,
                "max": 99,
                "id": "id_client_age",
                "data-target-audience": target_audience,
            }
        )

    def clean_client_age(self):
        age = self.cleaned_data["client_age"]
        error = get_age_validation_error(age, self.target_audience)
        if error:
            raise ValidationError(error)
        return age

    def clean_photo_front(self):
        return _validate_upload(
            self.cleaned_data.get("photo_front"),
            HAIR_PHOTO_EXTENSIONS,
            HAIR_PHOTO_CONTENT_TYPES,
            _("Front photo"),
        )

    def clean_photo_side(self):
        return _validate_upload(
            self.cleaned_data.get("photo_side"),
            HAIR_PHOTO_EXTENSIONS,
            HAIR_PHOTO_CONTENT_TYPES,
            _("Side photo"),
        )

    def clean_photo_back(self):
        return _validate_upload(
            self.cleaned_data.get("photo_back"),
            HAIR_PHOTO_EXTENSIONS,
            HAIR_PHOTO_CONTENT_TYPES,
            _("Back photo"),
        )


class WizardStep4Form(forms.ModelForm):
    """Step 4 — Payment method, proof of payment and final consent."""

    final_consent = forms.BooleanField(
        required=True,
        label=_(
            "I confirm the deposit has been transferred and I agree to the "
            "cancellation and refund policy."
        ),
        error_messages={
            "required": _("You must agree to the policy to submit your request."),
        },
    )

    # Declared as FileField (not the model's ImageField) so PDFs are accepted.
    proof_of_payment = forms.FileField(
        required=True,
        help_text=_("JPG, PNG or PDF — max 5 MB."),
    )

    class Meta:
        model = AppointmentRequest
        fields = ["payment_method_fk", "proof_of_payment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active payment methods, ordered by display_order
        self.fields["payment_method_fk"].queryset = PaymentMethod.objects.filter(
            is_active=True
        )
        self.fields["payment_method_fk"].required = True
        self.fields["payment_method_fk"].label_from_instance = lambda obj: obj.name
        self.fields["payment_method_fk"].empty_label = None
        self.fields["payment_method_fk"].widget.attrs.update({"class": "sr-only peer"})
        self.fields["proof_of_payment"].widget.attrs.update(
            {
                "accept": "image/jpeg,image/png,application/pdf",
                "class": _FILE_INPUT_CLASS,
            }
        )

    def clean_proof_of_payment(self):
        return _validate_upload(
            self.cleaned_data.get("proof_of_payment"),
            PROOF_EXTENSIONS,
            PROOF_CONTENT_TYPES,
            _("Proof of payment"),
        )
