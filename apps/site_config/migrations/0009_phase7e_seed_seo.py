"""Seed GlobalSEO defaults + PageSEO records for static pages.

Static pages seeded (from spec §9.3):
    '/', '/about/', '/contact/', '/terms/', '/privacy/', '/services/'

NOT seeded here:
    - Individual service pages (PageSEO with service FK) — these are created
      on-demand by the admin as services are added.
    - Consultation wizard — URL is dynamic (/bookings/book/<service_pk>/),
      not a static path. Not seeded per spec design.

Each PageSEO gets a HU translation with sensible defaults.
The admin can add EN/DE translations and edit all content.

Idempotent: checks existence before creating.
"""
from django.db import migrations

# Static page URL paths to seed
STATIC_PAGES = ['/', '/about/', '/contact/', '/terms/', '/privacy/', '/services/']


def seed_seo(apps, schema_editor):
    GlobalSEO = apps.get_model("site_config", "GlobalSEO")
    GlobalSEOTranslation = apps.get_model("site_config", "GlobalSEOTranslation")
    PageSEO = apps.get_model("site_config", "PageSEO")
    PageSEOTranslation = apps.get_model("site_config", "PageSEOTranslation")

    # ── GlobalSEO singleton ───────────────────────────────────
    global_seo, _created = GlobalSEO.objects.get_or_create(
        pk=1,
        defaults={
            "canonical_site_url": "https://afrikaihajfonas.hu",
            "google_verification": "",
            "bing_verification": "",
        },
    )

    # HU global defaults
    GlobalSEOTranslation.objects.get_or_create(
        global_seo=global_seo,
        language="hu",
        defaults={
            "default_meta_title": "Afrikai Hajfonás — Afrikai Hajfonás Budapest",
            "default_meta_description": (
                "Autentikus afrikai hajfonás Budapesten. "
                "Knotless box braids, cornrows és többé."
            ),
            "default_og_title": "Afrikai Hajfonás",
            "default_og_description": "Autentikus afrikai hajfonás Budapesten",
        },
    )

    # ── PageSEO for static pages ──────────────────────────────
    PAGE_META = {
        "/": {
            "meta_title": "Afrikai Hajfonás — Afrikai Hajfonás Budapest",
            "meta_description": (
                "Élje át az időtlen szépséget és a bonyolult mintákat, "
                "szenvedéllyel és hagyománnyal kézzel készítve."
            ),
        },
        "/about/": {
            "meta_title": "Rólunk — Afrikai Hajfonás",
            "meta_description": (
                "Ismerje meg a szalonunk történetét és a szenvedélyünket "
                "az autentikus afrikai hajfonás iránt."
            ),
        },
        "/contact/": {
            "meta_title": "Kapcsolat — Afrikai Hajfonás",
            "meta_description": (
                "Lépjen kapcsolatba velünk. Cím, telefonszám, e-mail és "
                "nyitvatartási idő."
            ),
        },
        "/terms/": {
            "meta_title": "Általános Szerződési Feltételek — Afrikai Hajfonás",
            "meta_description": "Az általános szerződési feltételek.",
        },
        "/privacy/": {
            "meta_title": "Adatvédelmi Tájékoztató — Afrikai Hajfonás",
            "meta_description": "Adatvédelmi tájékoztató.",
        },
        "/services/": {
            "meta_title": "Szolgáltatások — Afrikai Hajfonás",
            "meta_description": (
                "Böngéssze szolgáltatásainkat: knotless box braids, cornrows, "
                "twist braids és további afrikai hajfonási stílusok."
            ),
        },
    }

    for url_path in STATIC_PAGES:
        page_seo, _created = PageSEO.objects.get_or_create(
            url_path=url_path,
            defaults={"is_active": True, "service": None},
        )
        meta = PAGE_META.get(url_path, {})
        PageSEOTranslation.objects.get_or_create(
            page_seo=page_seo,
            language="hu",
            defaults={
                "meta_title": meta.get("meta_title", ""),
                "meta_description": meta.get("meta_description", ""),
                "og_title": "",
                "og_description": "",
            },
        )


def remove_seo(apps, schema_editor):
    GlobalSEO = apps.get_model("site_config", "GlobalSEO")
    GlobalSEOTranslation = apps.get_model("site_config", "GlobalSEOTranslation")
    PageSEO = apps.get_model("site_config", "PageSEO")
    PageSEOTranslation = apps.get_model("site_config", "PageSEOTranslation")
    PageSEOTranslation.objects.all().delete()
    PageSEO.objects.all().delete()
    GlobalSEOTranslation.objects.all().delete()
    GlobalSEO.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_config", "0008_phase7e_seo_models"),
        ("services", "0006_service_discount_percentage_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_seo, remove_seo),
    ]
