"""
Phase 7C — Email Template Rendering Service

Security (Decision #33):
    Uses regex-based {{ key }} substitution — NOT Django's template engine.
    This prevents admin-authored template tag injection ({% load %}, {% include %}).
    Admins get ONLY {{ placeholder }} syntax, nothing more.

Language Selection (§7.3):
    Transactional emails are sent using the appointment's stored customer_language.
    The caller passes the language explicitly. Falls back to 'hu' (base) if the
    requested language has no translation.

Placeholder Handling (§7.4):
    Unknown placeholders render as empty strings at runtime (no crashes).
    At authoring time, admin form validation warns about typos.
"""
import re

# ── Canonical Placeholder Vocabulary (Developer-Controlled) ────
# This is the complete set of placeholders the admin is permitted to use.
# Any {{ key }} not in this dict is flagged as unknown during validation.
#
# Key naming follows the spec §7.4 convention:
#   {{ entity_field }} e.g. {{ client_name }}, {{ service_name }}

EMAIL_PLACEHOLDERS = {
    # ── Client ────────────────────────────────────────────────
    "client_name": "Customer full name",
    "client_email": "Customer email address",
    "client_phone": "Customer phone number",
    "client_age": "Customer age",
    # ── Appointment ───────────────────────────────────────────
    "appointment_date": "Requested appointment date",
    "appointment_time": "Requested appointment time",
    "appointment_status": "Current appointment status label",
    "held_until": "Hold expiry deadline (date + time)",
    "payment_reference": "Payment reference code (AFH-XXXXXX)",
    # ── Service ───────────────────────────────────────────────
    "service_name": "Service name",
    "service_description": "Service description",
    "service_duration": "Service duration",
    "service_price": "Service base price",
    "selected_options": "Selected service options summary",
    # ── Provider ──────────────────────────────────────────────
    "provider_name": "Stylist / provider name",
    # ── Payment ───────────────────────────────────────────────
    "deposit_amount": "Required deposit amount",
    "payment_method_name": "Payment method name",
    "payment_details": "Payment method details (from snapshot)",
    # ── Business ──────────────────────────────────────────────
    "salon_name": "Salon business name",
    "salon_address": "Salon street address",
    "salon_phone": "Salon phone number",
    "salon_email": "Salon email address",
    "business_hours": "Business operating hours",
    "google_maps_link": "Google Maps URL",
    "website_url": "Website URL",
    # ── Social ────────────────────────────────────────────────
    "instagram_url": "Instagram profile URL",
    "facebook_url": "Facebook page URL",
    "tiktok_url": "TikTok profile URL",
    # ── Useful Links ──────────────────────────────────────────
    "guest_lookup_url": "Guest lookup / status page URL",
    "privacy_policy_url": "Privacy policy page URL",
    "terms_url": "Terms & conditions page URL",
    # ── Admin-Specific (expiry_reminder only) ────────────────
    # These are not in the spec §7.4 canonical list but are necessary for
    # the admin-facing expiry reminder email. Documented here for validation.
    "admin_url": "Direct link to admin review page for this appointment",
    "hours": "Hours remaining until hold expiry (reminder emails only)",
}

# Regex: matches {{ word }} where word is alphanumeric + underscore
_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def find_placeholders(text):
    """Return a set of all placeholder keys found in the text."""
    if not text:
        return set()
    return set(_PLACEHOLDER_RE.findall(text))


def find_unknown_placeholders(text):
    """Return a sorted list of placeholder keys in text that are NOT in
    the canonical EMAIL_PLACEHOLDERS vocabulary.

    Used by admin validation to catch typos before a broken email goes out.
    """
    found = find_placeholders(text)
    unknown = found - set(EMAIL_PLACEHOLDERS)
    return sorted(unknown)


def render_text(text, context):
    """Replace {{ key }} placeholders with values from context dict.

    Unknown keys (not in context) render as empty string — per spec §7.4,
    "Unsupported variables render as empty strings (no crashes)."

    This is regex-based, NOT Django template engine — per Decision #33.
    """
    if not text:
        return ""

    def _replace(match):
        key = match.group(1)
        value = context.get(key, "")
        return str(value) if value is not None else ""

    return _PLACEHOLDER_RE.sub(_replace, text)


def render_email(email_type, context, language="hu"):
    """Look up and render an email template.

    Args:
        email_type: EmailTemplate.EMAIL_TYPES key (e.g. 'expiry_reminder').
        context:    Dict of placeholder values.
        language:   Target language code ('hu', 'en', 'de').

    Returns:
        (subject, body_text, body_html) tuple, or None if:
          - No EmailTemplate exists for email_type, or
          - Template is_active=False, or
          - No translation exists for language AND no HU fallback.

    Language fallback chain: requested language → 'hu' (base).
    """
    from .models import EmailTemplate, EmailTemplateTranslation

    try:
        template = EmailTemplate.objects.get(email_type=email_type)
    except EmailTemplate.DoesNotExist:
        return None

    if not template.is_active:
        return None

    # Language fallback: requested language → 'hu' (base)
    translation = template.translations.filter(language=language).first()
    if translation is None:
        translation = template.translations.filter(language="hu").first()
    if translation is None:
        # No translation at all — nothing to send
        return None

    subject = render_text(translation.subject, context)
    body_text = render_text(translation.body_text, context)
    body_html = render_text(translation.body_html, context) if translation.body_html else ""

    return subject, body_text, body_html
