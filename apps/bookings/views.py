from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from apps.services.models import Service
from apps.providers.models import Provider
from .utils import get_available_slots

def book_service_view(request, service_pk):
    """
    Renders the main booking wizard checkout page for a selected service.
    """
    service = get_object_or_404(Service, pk=service_pk)
    
    # Pre-filter providers who are capable of doing this service
    providers = service.providers.all()
    
    context = {
        'service': service,
        'providers': providers,
        'today': datetime.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'bookings/book_service.html', context)

def load_available_slots_view(request):
    """
    HTMX-driven endpoint. Accepts provider_id, date, and service_id parameters,
    calculates empty schedule intervals, and returns only the HTML partial.
    """
    provider_id = request.GET.get('provider')
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')
    
    if not (provider_id and date_str and service_id):
        return HttpResponse('<p class="text-sm text-gray-500">Please select a stylist and date first.</p>')
        
    try:
        provider = Provider.objects.get(pk=provider_id)
        service = Service.objects.get(pk=service_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, Provider.DoesNotExist, Service.DoesNotExist):
        return HttpResponse('<p class="text-sm text-red-500">Invalid booking parameters selected.</p>')
        
    slots = get_available_slots(provider, target_date, service)
    
    context = {
        'slots': slots,
    }
    return render(request, 'bookings/partials/time_slots.html', context)
