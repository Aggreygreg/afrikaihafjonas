from django.shortcuts import render
from apps.services.models import Service
# SiteConfiguration import is no longer needed here

def homepage_view(request):
    # Fetch up to 10 services marked as 'is_popular'
    # select_related loads the category and parent category in a single query
    services = Service.objects.filter(is_popular=True).select_related('category__parent')[:10]
    
    context = {
        "services": services,
    }
    return render(request, "home.html", context)