"""
Tests for technical SEO features (ARCHITECTURAL_PRINCIPLES §9.5).

Covers:
- sitemap.xml index generation and section sitemaps
- robots.txt content and directives
- JSON-LD LocalBusiness structured data rendering in base.html
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.services.models import Service
from apps.site_config.models import SiteConfiguration


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SitemapTests(TestCase):
    """Verify sitemap index + section sitemaps return correct XML."""

    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(
            title="Knotless Box Braids",
            description="Test service.",
            base_price=55000,
            duration_minutes=360,
        )

    def test_sitemap_index_returns_xml(self):
        """GET /sitemap.xml returns XML with links to section sitemaps."""
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp["Content-Type"])
        # Should reference both static and services sections
        content = resp.content.decode()
        self.assertIn("sitemap-static.xml", content)
        self.assertIn("sitemap-services.xml", content)
    def test_static_sitemap_has_expected_urls(self):
        """Static sitemap includes homepage, about, contact, terms, privacy, services."""
        resp = self.client.get("/sitemap-static.xml")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        for expected in ["/about/", "/contact/", "/terms/", "/privacy/", "/services/"]:
            self.assertIn(expected, content)

    def test_services_sitemap_includes_service_detail(self):
        """Services sitemap includes a URL for each Service."""
        resp = self.client.get("/sitemap-services.xml")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # The service detail URL should be present
        expected_url = reverse("services:service_detail", kwargs={"pk": self.service.pk})
        self.assertIn(expected_url, content)


class RobotsTxtTests(TestCase):
    """Verify robots.txt content."""

    def test_robots_txt_returns_text(self):
        """GET /robots.txt returns text/plain with correct directives."""
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/plain")
        content = resp.content.decode()
        # Should allow all and disallow admin
        self.assertIn("User-agent: *", content)
        self.assertIn("Allow: /", content)
        self.assertIn("Disallow: /admin/", content)
        self.assertIn("Disallow: /bookings/book/", content)
        self.assertIn("Disallow: /bookings/status/", content)
        self.assertIn("Sitemap:", content)
        self.assertIn("/sitemap.xml", content)


class JsonLdTests(TestCase):
    """Verify JSON-LD structured data renders in pages."""

    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        self.config.business_name = "Afrikai Hajfonás"
        self.config.salon_phone = "+3612345678"
        self.config.salon_email = "info@afrikaihajfonas.hu"
        self.config.salon_address = "Budapest, Test Street 1"
        self.config.social_instagram = "https://instagram.com/test"
        self.config.save()

    def test_homepage_contains_jsonld_hairsalon(self):
        """Homepage HTML contains JSON-LD script with HairSalon type."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("application/ld+json", content)
        self.assertIn('"@type": "HairSalon"', content)
        self.assertIn("Afrikai Hajfonás", content)
        self.assertIn("+3612345678", content)
        self.assertIn("https://instagram.com/test", content)

    def test_jsonld_omits_empty_fields(self):
        """JSON-LD should not render telephone if empty."""
        self.config.salon_phone = ""
        self.config.save()
        resp = self.client.get("/")
        content = resp.content.decode()
        self.assertIn("application/ld+json", content)
        self.assertNotIn('"telephone"', content)
