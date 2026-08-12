from datetime import date, datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.providers.models import Provider
from apps.services.models import Service

from .forms import WizardStep3Form, WizardStep4Form
from .models import AppointmentRequest
from .utils import calculate_deposit, get_available_slots


# ── Small presentation helpers (formatting only — no business logic) ─
def _format_huf(amount):
    """Format an integer/Decimal amount as zero-decimal HUF: '20,000 Ft'."""
    try:
        return "{:,} Ft".format(int(amount))
    except (TypeError, ValueError):
        return "0 Ft"


def _build_options_snapshot(service, selected_ids):
    """
    Frozen historical snapshot of the client's selected ServiceOptions.

    Stored on AppointmentRequest.selected_options (JSONField) so the record
    retains the exact options chosen at request time even if the service's
    options change later.
    """
    if not selected_ids:
        return []
    options = service.options.filter(id__in=selected_ids)
    return [
        {
            "id": opt.id,
            "group": opt.group_name,
            "value": opt.value,
            "price": str(opt.additional_price),
        }
        for opt in options
    ]


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
            "discount_amount": service.base_price - service.discounted_price,
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
            "discount_amount": service.base_price - service.discounted_price,
        }
        return render(request, "bookings/partials/wizard_step_2.html", context)

    if action == "advance_to_step3":
        # Persist the scheduling selection (provider + date + time) and
        # navigate to the standalone Step 3 page (which needs a multipart
        # form for file uploads, so it cannot be an HTMX swap).
        provider_id = request.POST.get("provider")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time_slot")

        scheduling_ok = False
        provider = target_date = target_time = None
        if provider_id and date_str and time_str:
            try:
                provider = Provider.objects.get(pk=provider_id, services=service)
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                target_time = datetime.strptime(time_str, "%H:%M").time()
                scheduling_ok = True
            except (ValueError, Provider.DoesNotExist):
                scheduling_ok = False

        if not scheduling_ok:
            context = {
                "service": service,
                "providers": service.providers.all(),
                "today": date.today().isoformat(),
                "current_step": 2,
                "deposit": calculate_deposit(service.discounted_price),
                "discount_amount": service.base_price - service.discounted_price,
                "scheduling_error": _(
                    "Please select a stylist, date and an available time slot "
                    "before continuing."
                ),
            }
            return render(request, "bookings/partials/wizard_step_2.html", context)

        request.session[session_key]["provider_id"] = provider.id
        request.session[session_key]["target_date"] = target_date.isoformat()
        request.session[session_key]["target_time"] = target_time.strftime("%H:%M")
        request.session[session_key]["step"] = 3
        request.session.modified = True

        # HTMX follows the 302 and performs a full navigation to Step 3.
        return redirect("bookings:wizard_step_3", service_pk=service_pk)

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
            "discount_amount": service.base_price - service.discounted_price,
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
    return render(request, "bookings/booking_status_placeholder.html")


# ── Wizard Step 3: Client Details & Hair Data ─────────────────
def wizard_step_3(request, service_pk):
    """
    Step 3 — Client details, hair data and photos.

    GET: display the multipart form (client info + hair length cards +
         three photo uploads + GDPR consent).
    POST: validate and create the AppointmentRequest (draft approach —
          payment data is added in Step 4). The new record's id is stored in
          the session so Step 4 can update it.
    """
    service = get_object_or_404(Service, pk=service_pk)
    session_key = f"consult_{service_pk}"
    state = request.session.get(session_key, {})

    # Guard: scheduling must be complete before reaching Step 3.
    provider_id = state.get("provider_id")
    date_str = state.get("target_date")
    time_str = state.get("target_time")
    if not (provider_id and date_str and time_str):
        return redirect("bookings:book_service", service_pk=service_pk)

    provider = get_object_or_404(Provider, pk=provider_id)
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    target_time = datetime.strptime(time_str, "%H:%M").time()

    if request.method == "POST":
        form = WizardStep3Form(
            request.POST, request.FILES,
            target_audience=service.target_audience,
        )
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.service = service
            appointment.provider = provider
            appointment.selected_options = _build_options_snapshot(
                service, state.get("selected_options", [])
            )
            appointment.target_date = target_date
            appointment.target_time = target_time
            appointment.deposit_amount = calculate_deposit(
                service.discounted_price
            )
            appointment.status = AppointmentRequest.Status.PENDING_VERIFICATION
            # proof_of_payment + payment_method intentionally left blank —
            # they are set in Step 4 (Decision #14, draft approach).
            appointment.save()

            state["appointment_request_id"] = appointment.id
            state["step"] = 4
            request.session[session_key] = state
            request.session.modified = True

            return redirect("bookings:wizard_step_4", service_pk=service_pk)
    else:
        form = WizardStep3Form(target_audience=service.target_audience)

    from django.utils.formats import date_format

    context = {
        "service": service,
        "provider": provider,
        "form": form,
        "current_step": 3,
        "target_audience": service.target_audience,
        "target_date_display": date_format(target_date, "l, j F Y"),
        "target_time_display": target_time.strftime("%H:%M"),
        "deposit": calculate_deposit(service.discounted_price),
        "discount_amount": service.base_price - service.discounted_price,
        "deposit_formatted": _format_huf(
            calculate_deposit(service.discounted_price)
        ),
    }
    return render(request, "bookings/partials/wizard_step_3.html", context)


# ── Wizard Step 4: Finances & Submission ──────────────────────
def wizard_step_4(request, service_pk):
    """
    Step 4 — Deposit, payment reference, payment method and proof upload.

    GET: display the created AppointmentRequest (deposit amount, AFH-XXXXXX
         reference with copy button, booking recap) and the payment form.
    POST: attach payment_method + proof_of_payment to the existing record,
          refresh the 12-hour hold, and redirect to the confirmation page.
    """
    service = get_object_or_404(Service, pk=service_pk)
    session_key = f"consult_{service_pk}"
    state = request.session.get(session_key, {})
    appointment_id = state.get("appointment_request_id")

    if not appointment_id:
        # No draft request created yet — start the wizard from the beginning.
        return redirect("bookings:book_service", service_pk=service_pk)

    appointment = get_object_or_404(
        AppointmentRequest, pk=appointment_id, service=service,
    )

    if request.method == "POST":
        form = WizardStep4Form(request.POST, request.FILES, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            # Refresh the 12-hour hold window from the moment of submission.
            appointment.held_until = timezone.now() + timedelta(hours=12)
            appointment.save()

            # Hand off to the confirmation page via the reference code.
            return redirect(
                "bookings:confirmation",
                reference=appointment.payment_reference,
            )
    else:
        form = WizardStep4Form(instance=appointment)

    from django.utils.formats import date_format

    context = {
        "service": service,
        "appointment": appointment,
        "form": form,
        "current_step": 4,
        "deposit_formatted": _format_huf(appointment.deposit_amount),
        "target_date_display": date_format(appointment.target_date, "l, j F Y"),
        "target_time_display": appointment.target_time.strftime("%H:%M"),
    }
    return render(request, "bookings/partials/wizard_step_4.html", context)


# ── Confirmation Page ─────────────────────────────────────────
def confirmation(request, reference):
    """
    Confirmation page shown after a successful Step 4 submission.

    Displays the (large, copyable) payment reference, next steps, a reminder
    to save the reference, and a link to the Guest Lookup page.
    """
    appointment = get_object_or_404(
        AppointmentRequest, payment_reference=reference,
    )

    from django.utils.formats import date_format

    context = {
        "appointment": appointment,
        "deposit_formatted": _format_huf(appointment.deposit_amount),
        "target_date_display": date_format(appointment.target_date, "l, j F Y"),
        "target_time_display": appointment.target_time.strftime("%H:%M"),
    }
    return render(request, "bookings/confirmation.html", context)
