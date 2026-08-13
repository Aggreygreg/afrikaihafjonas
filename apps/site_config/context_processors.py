import json

from .models import SiteConfiguration
from .seo_service import resolve_seo

def site_config(request):
    """
    Makes the SiteConfiguration object available to all templates
    as a global variable named 'config'.
    """
    try:
        config = SiteConfiguration.objects.get()
    except SiteConfiguration.DoesNotExist:
        # In case the object hasn't been created in the admin yet
        config = None

    return {'config': config}


def _build_jsonld_localbusiness(config):
    """Build JSON-LD HairSalon structured data from SiteConfiguration.

    Returns a JSON string (safe to render with |safe) or empty string
    if no config exists. Only includes fields that have values — avoids
    trailing-comma issues that template-based JSON would have.
    """
    if config is None:
        return ""

    data = {
        "@context": "https://schema.org",
        "@type": "HairSalon",
        "name": config.business_name or "Afrikai Hajfonás",
        "priceRange": "$$",
    }

    if config.salon_phone:
        data["telephone"] = config.salon_phone
    if config.salon_email:
        data["email"] = config.salon_email
    if config.website_url:
        data["url"] = config.website_url
    if config.salon_address:
        data["address"] = {
            "@type": "PostalAddress",
            "streetAddress": config.salon_address,
        }
    if config.google_maps_link:
        data["hasMap"] = config.google_maps_link
    if config.business_hours:
        data["openingHours"] = config.business_hours.replace("\n", " ").strip()

    same_as = []
    if config.social_instagram:
        same_as.append(config.social_instagram)
    if config.social_facebook:
        same_as.append(config.social_facebook)
    if config.social_tiktok:
        same_as.append(config.social_tiktok)
    if same_as:
        data["sameAs"] = same_as

    return json.dumps(data, ensure_ascii=False)


def seo(request):
    """Resolve SEO metadata for the current page.

    Uses request.path to match static PageSEO records.
    For service detail pages, the view can set request.seo_service
    to override the URL-path matching.

    Also injects JSON-LD LocalBusiness structured data (§9.5).
    """
    # Allow views to explicitly pass a service for SEO resolution
    service = getattr(request, 'seo_service', None)

    seo_data = resolve_seo(
        url_path=request.path if service is None else None,
        service=service,
    )

    # JSON-LD LocalBusiness structured data
    config = getattr(request, '_site_config_cache', None)
    if config is None:
        try:
            config = SiteConfiguration.objects.get()
        except SiteConfiguration.DoesNotExist:
            config = None

    return {
        'seo': seo_data,
        'jsonld': _build_jsonld_localbusiness(config),
    }