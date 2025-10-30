from django.shortcuts import render
from apps.services.models import Service
from apps.site_config.models import SiteConfiguration

def homepage_view(request):
    # Fetch up to 5 services to display on the homepage
    services = Service.objects.all()[:5]
    # Fetch the one and only SiteConfiguration object
    config = SiteConfiguration.objects.get()
    
    context = {
        "services": services,
        # "config": config,  # No longer needed as it's provided by the context processor
    }
    return render(request, "home.html", context)