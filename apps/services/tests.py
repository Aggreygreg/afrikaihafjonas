from django.test import TestCase

from apps.services.models import ParentCategory, ServiceCategory, Service


class ServiceListHTMXTests(TestCase):
    """Regression tests for the catalog HTMX wiring.

    Bug fixed 2026-08-18: service_list.html used hx-get / hx-trigger and called
    htmx.trigger() without ever loading the HTMX runtime, so live filtering
    (gender tabs, debounced search) was dead. The runtime must be included on
    this template (the base template intentionally does not bundle it).
    """

    @classmethod
    def setUpTestData(cls):
        cls.women = ParentCategory.objects.create(name="Women's Braids")
        cls.children = ParentCategory.objects.create(name="Children's Braids")
        cls.womens_cat = ServiceCategory.objects.create(parent=cls.women, name="Knotless")
        cls.childrens_cat = ServiceCategory.objects.create(parent=cls.children, name="Kids Cornrows")
        cls.womens_service = Service.objects.create(
            category=cls.womens_cat,
            title="Knotless Box Braids",
            description="Classic knotless braids",
            target_audience="adults",
            base_price=45000,
            discount_percentage=0,
            duration_minutes=240,
        )
        cls.childrens_service = Service.objects.create(
            category=cls.childrens_cat,
            title="Kids Cornrows Simple",
            description="Simple cornrows for kids",
            target_audience="children",
            base_price=15000,
            discount_percentage=10,
            duration_minutes=90,
        )

    def test_htmx_runtime_loaded_on_catalog_page(self):
        """The HTMX <script> include must be present — without it, gender tabs
        throw `htmx is not defined` and search/filter triggers are inert."""
        response = self.client.get("/services/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "htmx.org", count=1)

    def test_htmx_request_returns_partial_only(self):
        """HX-Request header must render the partial whose root is
        #services-wrapper (the hx-target), not the full page."""
        response = self.client.get("/services/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "services/partials/service_grid.html")
        self.assertTemplateNotUsed(response, "services/service_list.html")
        self.assertContains(response, 'id="services-wrapper"', count=1)
        # Base page chrome must NOT be swapped into the target
        self.assertNotContains(response, "<!DOCTYPE html>")

    def test_plain_request_returns_full_page(self):
        """Non-HTMX (native form fallback / direct navigation) still gets the
        full page — the no-JS "Apply Filters" submit path depends on this."""
        response = self.client.get("/services/")
        self.assertTemplateUsed(response, "services/service_list.html")

    def test_gender_filter_param_flows_in_both_modes(self):
        """The gender query param must drive filtering in BOTH the HTMX
        partial request and the native full-page GET fallback.

        Uses Children's Braids deliberately: the view's gender lookup uses
        name__icontains, and "Women's Braids" *contains* the substring
        "men's braids" — so a Men's-vs-Women's assertion is order-dependent
        (known view bug, reported separately, not fixed here).
        """
        htmx_response = self.client.get(
            "/services/", {"gender": "Children's Braids"}, HTTP_HX_REQUEST="true"
        )
        self.assertContains(htmx_response, "Kids Cornrows Simple")
        self.assertNotContains(htmx_response, "Knotless Box Braids")

        full_response = self.client.get("/services/", {"gender": "Children's Braids"})
        self.assertContains(full_response, "Kids Cornrows Simple")
        self.assertNotContains(full_response, "Knotless Box Braids")
