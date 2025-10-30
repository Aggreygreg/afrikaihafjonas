from django.shortcuts import render, get_object_or_404
from .models import Service

def service_list_view(request):
    """
    Displays a list of all available services.
    """
    services = Service.objects.all().order_by('category', 'title')
    context = {
        'services': services,
    }
    return render(request, 'services/service_list.html', context)

def service_detail_view(request, pk):
    """
    Displays the detailed page for a single service.
    We prefetch related images and options for efficiency.
    """
    service = get_object_or_404(
        Service.objects.prefetch_related('images', 'options'),
        pk=pk
    )
    
    # Group the options by 'group_name' for the template
    # e.g., {'Length': [...], 'Color': [...], 'Add-on': [...]}
    options_grouped = {}
    for option in service.options.all():
        if option.group_name not in options_grouped:
            options_grouped[option.group_name] = []
        options_grouped[option.group_name].append(option)
    
    context = {
        'service': service,
        'grouped_options': options_grouped,
    }
    return render(request, 'services/service_detail.html', context)