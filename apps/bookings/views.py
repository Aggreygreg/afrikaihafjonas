from datetime import date, datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.providers.models import Provider
from apps.services.models import Service

from .utils import calculate_deposit, get_available_slots


def consult_wizard_view(request, service_pk):
    """
    Multi-step consultation wizard (Steps 1-2).

    Step 1: Configure service options (single-select required groups +
            multi-select optional add-on groups).
    Step 2: Select provider + schedule a date/time.

    State is persisted across steps via Django session (read-only phase —
    no AppointmentRequest objects are created here).

    The full-page GET renders the wizard shell; HTMX POST requests swap the
    step partials inside the ``#wizard-content`` target.
    """
    service = get_object_or_404(Service, pk=service_pk)
    session_key = f"consult_{service_pk}"

    # ── Full page load (non-HTMX): render wizard shell with step 1 ──
    if not request.htmx:
        # Initialise (or reset) the wizard session state.
        request.session[session_key] = {
            "step": 1,
            "selected_options": [],
            "provider_id": None,
            "target_date": None,
            "target_time": None,
        }
        request.session.modified = True

        options_by_group = service.get_options_grouped()
        providers = service.providers.all()
        context = {
            "service": service,
            "options_by_group": options_by_group,
            "providers": providers,
            "today": date.today().isoformat(),
            "current_step": 1,
            "deposit": calculate_deposit(service.discounted_price),
        }
        return render(request, "bookings/consult_wizard.html", context)

    # ── HTMX requests: step navigation ──
    action = request.POST.get("wizard_action", "")

    if action == "advance_to_step2":
        # Collect selected option IDs from POST.
        selected_ids = request.POST.getlist("selected_options")
        request.session[session_key]["selected_options"] = [
            int(x) for x in selected_ids if x.isdigit()
        ]
        request.session[session_key]["step"] = 2
        request.session.modified = True

        providers = service.providers.all()
        context = {
            "service": service,
            "providers": providers,
            "today": date.today().isoformat(),
            "current_step": 2,
            "deposit": calculate_deposit(service.discounted_price),
        }
        return render(request, "bookings/partials/wizard_step_2.html", context)

    if action == "back_to_step1":
        # Restore step 1 with the previously saved selections.
        saved_state = request.session.get(session_key, {})
        saved_option_ids = saved_state.get("selected_options", [])
        request.session[session_key]["step"] = 1
        request.session.modified = True

        options_by_group = service.get_options_grouped()
        context = {
            "service": service,
            "options_by_group": options_by_group,
            "selected_option_ids": saved_option_ids,
            "current_step": 1,
            "deposit": calculate_deposit(service.discounted_price),
        }
        return render(request, "bookings/partials/wizard_step_1.html", context)

    # Fallback for unknown actions.
    return HttpResponse("Invalid action", status=400)


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


def booking_status_placeholder_view(request):
    """Placeholder for the Guest Lookup Page — real implementation in Phase 4."""
    return render(request, 'bookings/booking_status_placeholder.html')
