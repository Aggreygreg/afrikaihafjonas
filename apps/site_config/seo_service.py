"""
Phase 7E — SEO Resolution Service

Fallback chain (spec §9.4):
    1. Page-level override (PageSEOTranslation for this page + active language)
    2. Global default (GlobalSEOTranslation for active language)
    3. Hardcoded dev fallback (sensible defaults)

Used by the seo context processor to inject meta tags into every template.
"""
from django.utils.translation import get_language


# ── Hardcoded dev fallback (spec §9.4 step 3) ─────────────────
# These are the safety net when no admin SEO config exists at all.
# They are developer-controlled and NOT admin-editable.
_DEV_FALLBACK = {
    "meta_title": "Afrikai Hajfonás — African Braiding in Budapest",
    "meta_description": (
        "Authentic African braiding salon in Budapest. "
        "Knotless braids, box braids, cornrows, and more."
    ),
    "og_title": "Afrikai Hajfonás",
    "og_description": "Authentic African Braiding in Budapest",
    "canonical_url": "",
    "og_image": "",
    "google_verification": "",
    "bing_verification": "",
}


def resolve_seo(url_path=None, service=None, language=None):
    """Resolve SEO metadata for a page.

    Args:
        url_path:  URL path for static pages (e.g., '/', '/about/').
        service:   Service instance for dynamic service pages.
        language:  Language code ('hu', 'en', 'de'). Defaults to active language.

    Returns:
        Dict with keys: meta_title, meta_description, og_title,
        og_description, canonical_url, og_image,
        google_verification, bing_verification.
    """
    from .models import GlobalSEO, GlobalSEOTranslation, PageSEO, PageSEOTranslation

    if language is None:
        language = (get_language() or "hu")[:2]

    result = dict(_DEV_FALLBACK)

    # ── Step 2: Global defaults ────────────────────────────────
    global_trans = None
    try:
        global_seo = GlobalSEO.get_solo()
        global_trans = (
            global_seo.translations.filter(language=language).first()
            or global_seo.translations.filter(language="hu").first()
        )
        if global_seo.canonical_site_url:
            result["canonical_url"] = global_seo.canonical_site_url
        if global_seo.og_image_default:
            result["og_image"] = global_seo.og_image_default.url
        if global_seo.google_verification:
            result["google_verification"] = global_seo.google_verification
        if global_seo.bing_verification:
            result["bing_verification"] = global_seo.bing_verification
    except Exception:
        pass  # Table not ready / not configured

    if global_trans:
        if global_trans.default_meta_title:
            result["meta_title"] = global_trans.default_meta_title
        if global_trans.default_meta_description:
            result["meta_description"] = global_trans.default_meta_description
        if global_trans.default_og_title:
            result["og_title"] = global_trans.default_og_title
        if global_trans.default_og_description:
            result["og_description"] = global_trans.default_og_description

    # ── Step 1: Page-level override (highest priority) ─────────
    page_trans = None
    try:
        page_seo_qs = PageSEO.objects.filter(is_active=True)
        if service is not None:
            page_seo = page_seo_qs.filter(service=service).first()
        elif url_path is not None:
            page_seo = page_seo_qs.filter(url_path=url_path).first()
        else:
            page_seo = None

        if page_seo:
            page_trans = (
                page_seo.translations.filter(language=language).first()
                or page_seo.translations.filter(language="hu").first()
            )
    except Exception:
        pass

    if page_trans:
        # Only override fields that are non-empty in the page-level translation
        if page_trans.meta_title:
            result["meta_title"] = page_trans.meta_title
        if page_trans.meta_description:
            result["meta_description"] = page_trans.meta_description
        if page_trans.og_title:
            result["og_title"] = page_trans.og_title
        if page_trans.og_description:
            result["og_description"] = page_trans.og_description

    return result
