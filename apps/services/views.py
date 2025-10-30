from django.shortcuts import render, get_object_or_404
from .models import Service

def service_list_view(request):
    """
    Displays a list of all available services.
    """
    services = Service.objects.all()
    context = {
        'services': services,
    }
    return render(request, 'services/service_list.html', context)

def service_detail_view(request, pk):
    """
    Displays the detailed page for a single service.
    """
    service = get_object_or_404(Service, pk=pk)
    context = {
        'service': service,
    }
    return render(request, 'services/service_detail.html', context)