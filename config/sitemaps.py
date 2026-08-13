"""
Sitemap configuration for technical SEO (ARCHITECTURAL_PRINCIPLES §9.5).

Two sitemap classes:
- StaticViewSitemap: fixed public-facing pages (homepage, about, contact, etc.)
- ServiceSitemap: one entry per Service detail page (dynamic, queryable)

Combined via a dict-based sitemap index in urls.py.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.services.models import Service


class StaticViewSitemap(Sitemap):
    """Static public pages that always exist."""

    changefreq = "monthly"
    priority = 0.8

    def items(self):
        # Return URL names; location() resolves them to paths.
        return [
            "homepage",
            "about",
            "contact",
            "terms",
            "privacy",
            "services:service_list",
        ]

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    """One URL per service detail page."""

    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Service.objects.all().order_by("pk")

    def location(self, service):
        return reverse("services:service_detail", kwargs={"pk": service.pk})
