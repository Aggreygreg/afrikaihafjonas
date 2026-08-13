from django.shortcuts import render

# Static site-level pages (About, Contact, Terms, Privacy).
#
# These pages are intentionally "fat models, skinny templates": the salon
# contact details live on the SiteConfiguration singleton, which is injected
# into every template via the `apps.site_config.context_processors.site_config`
# context processor as `{{ config.* }}`. The views therefore stay thin — they
# simply select the template to render.


def about_page(request):
    """Salon story, mission, team and membership badges."""
    return render(request, "pages/about.html")


def contact_page(request):
    """Salon address, phone, email, business hours, social links and map."""
    return render(request, "pages/contact.html")


def terms_page(request):
    """Terms & Conditions: deposit/hold, appointment request, photos, cancellation."""
    return render(request, "pages/terms.html")


def privacy_page(request):
    """GDPR-compliant Privacy Policy."""
    return render(request, "pages/privacy.html")
