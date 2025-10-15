from django.shortcuts import render
from apps.services.models import Service

def homepage_view(request):
    # Fetch up to 5 services to display on the homepage
    services = Service.objects.all()[:5]
    context = {
        "services": services,
    }
    return render(request, "home.html", context)