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


def seo(request):
    """Resolve SEO metadata for the current page.

    Uses request.path to match static PageSEO records.
    For service detail pages, the view can set request.seo_service
    to override the URL-path matching.
    """
    # Allow views to explicitly pass a service for SEO resolution
    service = getattr(request, 'seo_service', None)

    seo_data = resolve_seo(
        url_path=request.path if service is None else None,
        service=service,
    )
    return {'seo': seo_data}