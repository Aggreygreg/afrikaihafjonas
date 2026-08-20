from datetime import date, datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _

from apps.providers.models import Provider
from apps.services.models import Service

from .forms import WizardStep3Form, WizardStep4Form
from .models import AppointmentRequest, PaymentMethod
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
            "group": opt.display_group_name,
            "value": opt.display_value,
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
    return HttpResponse(str(_("Invalid action")), status=400)


def load_available_slots_view(request):
    """
    HTMX-driven endpoint. Accepts provider_id, date, and service_id parameters,
    calculates empty schedule intervals, and returns only the HTML partial.
    """
    provider_id = request.GET.get('provider')
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')

    if not (provider_id and date_str and service_id):
        return HttpResponse('<p class="text-sm text-gray-500">' + str(_("Please select a stylist and date first.")) + '</p>')

    try:
        provider = Provider.objects.get(pk=provider_id)
        service = Service.objects.get(pk=service_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, Provider.DoesNotExist, Service.DoesNotExist):
        return HttpResponse('<p class="text-sm text-red-500">' + str(_("Invalid booking parameters selected.")) + '</p>')

    slots = get_available_slots(provider, target_date, service)

    context = {
        'slots': slots,
    }
    return render(request, 'bookings/partials/time_slots.html', context)


# ── Guest Lookup Page (Journey 4) ─────────────────────────────
# Per-status display configuration (Decision #15). The headline message and
# badge colour are presentation concerns; the show/hide flags encode the
# client-visibility rules for each status.
_STATUS_DISPLAY = {
    AppointmentRequest.Status.PENDING_VERIFICATION: {
        "badge": "bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-200",
        "accent": "bg-amber-500",
        "headline": _(
            "We received your request and are verifying your deposit."
        ),
        "show_admin_notes": False,
        "show_provider": False,
        "show_verified_badge": False,
        "show_refund": False,
        "show_new_request_link": False,
    },
    AppointmentRequest.Status.PENDING_REVIEW: {
        "badge": "bg-blue-100 text-blue-800 ring-1 ring-inset ring-blue-200",
        "accent": "bg-blue-500",
        "headline": _(
            "Your deposit is verified! We're now reviewing your hair photos."
        ),
        "show_admin_notes": True,
        "show_provider": False,
        "show_verified_badge": True,
        "show_refund": False,
        "show_new_request_link": False,
    },
    AppointmentRequest.Status.APPROVED: {
        "badge": "bg-green-100 text-green-800 ring-1 ring-inset ring-green-200",
        "accent": "bg-green-600",
        "headline": _("Your appointment is confirmed!"),
        "show_admin_notes": True,
        "show_provider": True,
        "show_verified_badge": False,
        "show_refund": False,
        "show_new_request_link": False,
    },
    AppointmentRequest.Status.REJECTED: {
        "badge": "bg-red-100 text-red-800 ring-1 ring-inset ring-red-200",
        "accent": "bg-red-600",
        "headline": _("Unfortunately, your request was not approved."),
        "show_admin_notes": True,
        "show_provider": False,
        "show_verified_badge": False,
        "show_refund": True,
        "show_new_request_link": False,
    },
    AppointmentRequest.Status.EXPIRED: {
        "badge": "bg-gray-100 text-gray-700 ring-1 ring-inset ring-gray-300",
        "accent": "bg-gray-500",
        "headline": _(
            "Your request has expired. Your hold on this time slot has ended."
        ),
        "show_admin_notes": True,
        "show_provider": False,
        "show_verified_badge": False,
        "show_refund": False,
        "show_new_request_link": True,
    },
}


def _lookup_appointment(email, reference):
    """
    Run the guest lookup and build the template context.

    Returns a dict with either ``lookup_error`` (not found / missing input) or
    the full display context for a found ``AppointmentRequest``. Formatting
    only — no business logic.
    """
    from django.utils.formats import date_format

    if not email or not reference:
        return {
            "lookup_error": _(
                "Please enter both your email address and AFH reference code."
            )
        }

    appointment = (
        AppointmentRequest.objects
        .select_related("service", "provider", "payment_snapshot", "payment_method_fk")
        .filter(
            client_email__iexact=email,
            payment_reference__iexact=reference,
        ).first()
    )

    if appointment is None:
        return {
            "lookup_error": _(
                "No request found. Please check your email and reference code "
                "and try again."
            )
        }

    # Payment method name comes from the snapshot (frozen) — not live data.
    # Per Decision #31, detail_fields_snapshot is NEVER shown to customers.
    payment_method_display = None
    snapshot = getattr(appointment, "payment_snapshot", None)
    if snapshot:
        payment_method_display = snapshot.payment_method_name
    elif appointment.payment_method_fk:
        payment_method_display = appointment.payment_method_fk.display_name

    return {
        "appointment": appointment,
        "status_cfg": _STATUS_DISPLAY[appointment.status],
        "deposit_formatted": _format_huf(appointment.deposit_amount),
        "payment_method_display": payment_method_display,
        "target_date_display": date_format(appointment.target_date, "l, j F Y"),
        "target_time_display": appointment.target_time.strftime("%H:%M"),
    }


def guest_lookup_view(request):
    """
    Guest Lookup Page (``/bookings/status/``).

    GET:  render the lookup form (email + AFH reference code).
    POST: query ``AppointmentRequest`` by case-insensitive email + reference.
          HTMX POST returns just the result partial (swapped into
          ``#lookup-results``); a non-HTMX POST re-renders the full page with
          the result inlined.

    Proof-of-payment images and internal notes are NEVER rendered to clients
    (Decision #15).
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        reference = request.POST.get("payment_reference", "").strip()
        context = _lookup_appointment(email, reference)

        if request.htmx:
            return render(
                request,
                "bookings/partials/guest_lookup_result.html",
                context,
            )
        return render(request, "bookings/guest_lookup.html", context)

    return render(request, "bookings/guest_lookup.html")


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
            # Capture customer language at submission — immutable afterwards.
            # Per Decision #28, this drives all future email communication.
            appointment.customer_language = get_language()[:2]
            appointment.save()

            # Send 'request_received' confirmation email to the customer
            from .notifications import send_appointment_email
            send_appointment_email(appointment, "request_received", request)

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

            # Create the historical payment snapshot (Decision #27/#31).
            # Image-type fields are physically copied to payment_snapshots/<ref>/.
            appointment.create_payment_snapshot()

            # Send 'verification_pending' email — payment proof uploaded,
            # awaiting admin verification.
            from .notifications import send_appointment_email
            send_appointment_email(appointment, "verification_pending", request)

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


# ── HTMX: Payment Detail Fields ──────────────────────────────
def payment_detail_fields(request):
    """
    HTMX endpoint — returns active PaymentDetailField records for a given
    payment method ID. Used by Step 4 to show live payment instructions
    (IBAN, account holder, QR codes) when the customer selects a method.

    Per Decision #15/#31, these detail fields are shown ONLY here at Step 4
    payment time. They are NEVER shown in Guest Lookup or confirmation page.
    """
    if not request.htmx:
        return HttpResponse(status=403)

    method_id = request.GET.get("method_id")
    if not method_id:
        return HttpResponse("")

    method = get_object_or_404(PaymentMethod, pk=method_id, is_active=True)
    fields = method.detail_fields.filter(is_active=True).order_by("display_order")

    context = {
        "payment_method": method,
        "detail_fields": fields,
    }
    return render(
        request,
        "bookings/partials/_payment_detail_fields.html",
        context,
    )
