from datetime import datetime, date, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.providers.models import AvailabilityRule
from .models import AppointmentRequest


# ── Deposit Logic ─────────────────────────────────────────────
DEPOSIT_THRESHOLD = 45_000  # HUF
DEPOSIT_HIGH = 20_000       # HUF — for services >= threshold
DEPOSIT_LOW = 10_000        # HUF — for services < threshold


def calculate_deposit(base_price):
    """
    Fixed flat-rate deposit based on the service's base_price.
    >= 45,000 Ft -> 20,000 Ft
    <  45,000 Ft -> 10,000 Ft
    """
    if base_price >= DEPOSIT_THRESHOLD:
        return DEPOSIT_HIGH
    return DEPOSIT_LOW


# ── Time Slot Calculation ─────────────────────────────────────
def get_available_slots(provider, target_date, service):
    """
    Returns a list of available time objects (HH:MM) for a provider
    on a given date based on their availability rules and existing
    appointment requests.

    Rules:
      - 30-minute grid interval.
      - Slot renders only if start + service_duration <= shift end.
      - Slot is blocked if it overlaps with an AppointmentRequest
        where status == 'approved' OR held_until > now (active hold).
      - Past-time slots on today's date are blocked.
    """
    weekday = target_date.weekday()

    rule = AvailabilityRule.objects.filter(
        provider=provider, day_of_week=weekday
    ).first()
    if not rule:
        return []

    slot_interval = timedelta(minutes=30)
    service_duration = timedelta(minutes=service.duration_minutes)

    start_dt = datetime.combine(target_date, rule.start_time)
    end_dt = datetime.combine(target_date, rule.end_time)

    now = timezone.now()

    # Fetch existing requests that block the calendar:
    #   approved (confirmed) OR still within hold window
    blocking_requests = AppointmentRequest.objects.filter(
        provider=provider,
        target_date=target_date,
    ).filter(
        Q(status="approved") | Q(held_until__gt=now)
    )

    # Build occupied intervals
    occupied = []
    for req in blocking_requests:
        slot_start = datetime.combine(target_date, req.target_time)
        slot_end = slot_start + service_duration
        occupied.append((slot_start, slot_end))

    available_slots = []
    current_dt = start_dt

    while current_dt + service_duration <= end_dt:
        potential_start = current_dt
        potential_end = current_dt + service_duration

        is_overlapping = False
        for occ_start, occ_end in occupied:
            if potential_start < occ_end and potential_end > occ_start:
                is_overlapping = True
                break

        # Prevent past-time slots on today's date
        if target_date == date.today():
            now_naive = datetime.now()
            if potential_start < now_naive:
                is_overlapping = True

        if not is_overlapping:
            available_slots.append(potential_start.time())

        current_dt += slot_interval

    return available_slots
