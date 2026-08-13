"""
Appointment notification service — wires transactional email triggers.

Each function builds a canonical placeholder context dict from an AppointmentRequest
and sends the appropriate email via the Phase 7C rendering pipeline (render_email).

Language selection (Decision #28):
    Customer-facing emails use appointment.customer_language (captured at submission).
    Falls back to 'hu' (base language) if the requested language has no translation.

URL building:
    Views and admin actions pass `request` for build_absolute_uri().
    Management commands (no request) fall back to config.website_url + reverse().
"""
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from apps.site_config.email_service import render_email
from apps.site_config.models import SiteConfiguration


def _build_absolute_url(path, request=None):
    """Build an absolute URL from a path.

    Prefers request.build_absolute_uri() (views/admin).
    Falls back to config.website_url + path (commands/no-request context).
    """
    if request is not None:
        return request.build_absolute_uri(path)
    # No request — prepend the configured website URL
    try:
        config = SiteConfiguration.get_solo()
        base = (config.website_url or "").rstrip("/")
        if base:
            return base + path
    except Exception:
        pass
    return path


def _format_selected_options(appointment):
    """Format the frozen selected_options JSON as a readable string."""
    opts = appointment.selected_options
    if not opts:
        return ""
    # selected_options can be a list of dicts or an empty dict
    if isinstance(opts, dict):
        opts = list(opts.values()) if opts else []
    if not opts:
        return ""
    parts = []
    for opt in opts:
        if isinstance(opt, dict):
            parts.append(opt.get("value", str(opt)))
        else:
            parts.append(str(opt))
    return ", ".join(parts)


def _build_context(appointment, request=None):
    """Build the canonical placeholder context dict from an AppointmentRequest.

    Includes all 31 canonical placeholders. Values that don't apply to the
    specific appointment are set to empty string (render_text renders
    unknown/empty keys as empty strings per spec §7.4).
    """
    try:
        config = SiteConfiguration.get_solo()
    except Exception:
        config = None

    salon_name = getattr(config, "business_name", "") or "Afrikai Hajfonás"

    # Build absolute URLs for customer-facing links
    guest_lookup_url = ""
    privacy_url = ""
    terms_url = ""
    try:
        guest_lookup_url = _build_absolute_url(
            reverse("bookings:guest_lookup"), request
        )
        privacy_url = _build_absolute_url(reverse("privacy"), request)
        terms_url = _build_absolute_url(reverse("terms"), request)
    except Exception:
        pass  # URL conf not ready (e.g., during tests)

    # Payment method name — prefer snapshot (frozen), fall back to live FK
    payment_method_name = ""
    snapshot = getattr(appointment, "payment_snapshot", None)
    if snapshot:
        payment_method_name = snapshot.payment_method_name
    elif getattr(appointment, "payment_method_fk_id", None):
        if appointment.payment_method_fk:
            payment_method_name = appointment.payment_method_fk.name

    # Service info
    service = appointment.service
    service_name = service.title if service else ""
    service_description = getattr(service, "description", "") or "" if service else ""
    service_duration = service.formatted_duration if service else ""
    service_price = service.formatted_discounted_price if service else ""

    # Provider
    provider = appointment.provider
    provider_name = provider.display_name if provider else ""

    # Deposit formatting
    deposit_amount = ""
    if appointment.deposit_amount:
        try:
            deposit_amount = "{:,}".format(int(appointment.deposit_amount))
        except (TypeError, ValueError):
            deposit_amount = str(appointment.deposit_amount)

    # Held-until formatting
    held_until = ""
    if appointment.held_until:
        try:
            from django.utils import timezone
            held_until = timezone.localtime(appointment.held_until).strftime(
                "%Y-%m-%d %H:%M"
            )
        except Exception:
            held_until = str(appointment.held_until)

    return {
        # ── Client ──────────────────────────────────────────────
        "client_name": appointment.client_name or "",
        "client_email": appointment.client_email or "",
        "client_phone": appointment.client_phone or "",
        "client_age": str(appointment.client_age) if appointment.client_age else "",
        # ── Appointment ─────────────────────────────────────────
        "appointment_date": str(appointment.target_date) if appointment.target_date else "",
        "appointment_time": appointment.target_time.strftime("%H:%M") if appointment.target_time else "",
        "appointment_status": appointment.get_status_display(),
        "held_until": held_until,
        "payment_reference": appointment.payment_reference or "",
        # ── Service ─────────────────────────────────────────────
        "service_name": service_name,
        "service_description": service_description,
        "service_duration": service_duration,
        "service_price": service_price,
        "selected_options": _format_selected_options(appointment),
        # ── Provider ────────────────────────────────────────────
        "provider_name": provider_name,
        # ── Payment ─────────────────────────────────────────────
        "deposit_amount": deposit_amount,
        "payment_method_name": payment_method_name,
        "payment_details": "",
        # ── Business ────────────────────────────────────────────
        "salon_name": salon_name,
        "salon_address": getattr(config, "salon_address", "") or "",
        "salon_phone": getattr(config, "salon_phone", "") or "",
        "salon_email": getattr(config, "salon_email", "") or "",
        "business_hours": getattr(config, "business_hours", "") or "",
        "google_maps_link": getattr(config, "google_maps_link", "") or "",
        "website_url": getattr(config, "website_url", "") or "",
        # ── Social ──────────────────────────────────────────────
        "instagram_url": getattr(config, "social_instagram", "") or "",
        "facebook_url": getattr(config, "social_facebook", "") or "",
        "tiktok_url": getattr(config, "social_tiktok", "") or "",
        # ── Useful Links ────────────────────────────────────────
        "guest_lookup_url": guest_lookup_url,
        "privacy_policy_url": privacy_url,
        "terms_url": terms_url,
    }


def send_appointment_email(appointment, email_type, request=None):
    """Send a transactional email to the customer for this appointment.

    Args:
        appointment: AppointmentRequest instance.
        email_type:  EmailTemplate.EMAIL_TYPES key.
        request:     HttpRequest (for absolute URLs). Optional.

    Returns:
        True if email was sent, False if skipped (no template, inactive,
        or no client email).
    """
    if not appointment.client_email:
        return False

    language = getattr(appointment, "customer_language", None) or "hu"
    context = _build_context(appointment, request)

    rendered = render_email(email_type, context, language=language)
    if rendered is None:
        # No template configured or inactive — skip silently.
        return False

    subject, body_text, body_html = rendered

    try:
        config = SiteConfiguration.get_solo()
        from_name = config.business_name or "Afrikai Hajfonás"
    except Exception:
        from_name = "Afrikai Hajfonás"

    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject=subject,
        message=body_text,
        html_message=body_html if body_html else None,
        from_email=from_email,
        recipient_list=[appointment.client_email],
        fail_silently=True,  # Never crash the booking flow over email failure
    )
    return True
