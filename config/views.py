from django.shortcuts import render
from apps.services.models import Service
# SiteConfiguration import is no longer needed here

def homepage_view(request):
    # Fetch services marked as 'is_popular'
    services = Service.objects.filter(is_popular=True)[:5]
    
    context = {
        "services": services,
    }
    return render(request, "home.html", context)