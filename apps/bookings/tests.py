"""
Tests for the appointment notification system (Phase 7C email triggers).

Verifies that send_appointment_email():
1. Builds a complete context dict from an AppointmentRequest.
2. Sends the correct email via the rendering pipeline.
3. Respects customer_language for language selection.
4. Returns False gracefully when no template / inactive template / no email.
5. Handles missing optional data without crashing.
"""
from datetime import date, time, timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.bookings.models import AppointmentRequest, PaymentMethod, PaymentMethodTranslation
from apps.bookings.notifications import (
    send_appointment_email,
    _build_context,
    _format_selected_options,
)
from apps.providers.models import Provider
from apps.services.models import Service, ServiceTranslation
from apps.site_config.models import EmailTemplate


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationTests(TestCase):
    """End-to-end notification tests with in-memory email backend."""

    @classmethod
    def setUpTestData(cls):
        cls.provider = Provider.objects.create(display_name="Anna Stylist")
        cls.service = Service.objects.create(
            base_price=55000,
            duration_minutes=360,
        )
        ServiceTranslation.objects.create(
            service=cls.service, language="hu",
            title="Knotless Box Braids",
            description="Beautiful knotless braids.",
        )
        cls.payment_method = PaymentMethod.objects.create(
            slug="test-wise",
            is_active=True,
            display_order=99,
        )
        PaymentMethodTranslation.objects.create(
            payment_method=cls.payment_method, language="hu",
            name="Test Wise",
        )
        cls.appointment = AppointmentRequest.objects.create(
            service=cls.service,
            provider=cls.provider,
            client_name="Test Client",
            client_email="test@example.com",
            client_phone="+36301234567",
            client_age=25,
            hair_length=AppointmentRequest.HairLength.SHOULDER,
            photo_front="hair_photos/test_front.jpg",
            photo_side="hair_photos/test_side.jpg",
            photo_back="hair_photos/test_back.jpg",
            target_date=date(2026, 9, 15),
            target_time=time(14, 0),
            deposit_amount=20000,
            payment_reference="AFH-TEST01",
            payment_method_fk=cls.payment_method,
            customer_language="en",
            status=AppointmentRequest.Status.PENDING_VERIFICATION,
            held_until=timezone.now() + timedelta(hours=12),
        )

    def test_build_context_has_all_canonical_keys(self):
        """_build_context should return all 31 canonical placeholder keys."""
        ctx = _build_context(self.appointment)
        expected_keys = {
            "client_name", "client_email", "client_phone", "client_age",
            "appointment_date", "appointment_time", "appointment_status",
            "held_until", "payment_reference",
            "service_name", "service_description", "service_duration",
            "service_price", "selected_options",
            "provider_name",
            "deposit_amount", "payment_method_name", "payment_details",
            "salon_name", "salon_address", "salon_phone", "salon_email",
            "business_hours", "google_maps_link", "website_url",
            "instagram_url", "facebook_url", "tiktok_url",
            "guest_lookup_url", "privacy_policy_url", "terms_url",
        }
        self.assertEqual(set(ctx.keys()), expected_keys)

    def test_build_context_values_populated(self):
        """Context should contain actual appointment data."""
        ctx = _build_context(self.appointment)
        self.assertEqual(ctx["client_name"], "Test Client")
        self.assertEqual(ctx["payment_reference"], "AFH-TEST01")
        self.assertEqual(ctx["service_name"], "Knotless Box Braids")
        self.assertEqual(ctx["provider_name"], "Anna Stylist")
        self.assertEqual(ctx["payment_method_name"], "Test Wise")
        self.assertIn("20,000", ctx["deposit_amount"])

    def test_send_request_received_email(self):
        """send_appointment_email for 'request_received' sends one email."""
        result = send_appointment_email(self.appointment, "request_received")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("test@example.com", email.to)
        self.assertIn("AFH-TEST01", email.subject)

    def test_send_appointment_approved_email(self):
        """Verify 'appointment_approved' email."""
        result = send_appointment_email(self.appointment, "appointment_approved")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("test@example.com", mail.outbox[0].to)

    def test_send_appointment_rejected_email(self):
        """Verify 'appointment_rejected' email."""
        result = send_appointment_email(self.appointment, "appointment_rejected")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_payment_verified_email(self):
        """Verify 'payment_verified' email."""
        result = send_appointment_email(self.appointment, "payment_verified")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_refund_notification_email(self):
        """Verify 'refund_notification' email."""
        result = send_appointment_email(self.appointment, "refund_notification")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_appointment_expired_email(self):
        """Verify 'appointment_expired' email."""
        result = send_appointment_email(self.appointment, "appointment_expired")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_verification_pending_email(self):
        """Verify 'verification_pending' email."""
        result = send_appointment_email(self.appointment, "verification_pending")
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)

    def test_language_uses_customer_language(self):
        """Email body should be in customer_language (en), not base (hu)."""
        send_appointment_email(self.appointment, "request_received")
        email = mail.outbox[0]
        # EN body contains "Dear" — HU body contains "Kedves"
        self.assertIn("Dear", email.body)
        self.assertNotIn("Kedves", email.body)

    def test_language_falls_back_to_hu(self):
        """When customer_language='hu', HU template is used."""
        self.appointment.customer_language = "hu"
        self.appointment.save(update_fields=["customer_language"])
        send_appointment_email(self.appointment, "request_received")
        email = mail.outbox[0]
        self.assertIn("Kedves", email.body)

    def test_returns_false_for_no_client_email(self):
        """Appointment with empty email → returns False, no email sent."""
        self.appointment.client_email = ""
        self.appointment.save(update_fields=["client_email"])
        result = send_appointment_email(self.appointment, "request_received")
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_returns_false_for_inactive_template(self):
        """Inactive template → returns False, no email sent."""
        template = EmailTemplate.objects.get(email_type="request_received")
        template.is_active = False
        template.save()
        result = send_appointment_email(self.appointment, "request_received")
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_returns_false_for_unknown_email_type(self):
        """Non-existent email type → returns False."""
        result = send_appointment_email(self.appointment, "nonexistent_type")
        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)


class FormatSelectedOptionsTests(TestCase):
    """Tests for the _format_selected_options helper."""

    def test_empty_list(self):
        appt = type("Mock", (), {"selected_options": []})()
        self.assertEqual(_format_selected_options(appt), "")

    def test_empty_dict(self):
        appt = type("Mock", (), {"selected_options": {}})()
        self.assertEqual(_format_selected_options(appt), "")

    def test_list_of_dicts(self):
        appt = type("Mock", (), {"selected_options": [
            {"value": "Black", "price": "0"},
            {"value": "Waist Length", "price": "5000"},
        ]})()
        result = _format_selected_options(appt)
        self.assertIn("Black", result)
        self.assertIn("Waist Length", result)

    def test_none(self):
        appt = type("Mock", (), {"selected_options": None})()
        self.assertEqual(_format_selected_options(appt), "")
