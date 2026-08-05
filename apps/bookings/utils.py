from datetime import datetime, date, timedelta, time
from .models import Booking
from apps.providers.models import AvailabilityRule

def get_available_slots(provider, target_date, service):
    """
    Returns a list of available time objects (HH:MM) for a provider 
    on a given date based on their availability rules and existing bookings.
    """
    # 1. Get weekday (Django/Python weekday: 0 = Monday, 6 = Sunday)
    weekday = target_date.weekday()
    
    # 2. Fetch the provider's schedule rule for this weekday
    rule = AvailabilityRule.objects.filter(provider=provider, day_of_week=weekday).first()
    if not rule:
        return [] # Provider is not working on this day of the week
    
    # 3. Define time slot step (e.g., 30 minutes, or matching service duration)
    # Using a 30-minute grid is standard for salons to maximize scheduling efficiency
    slot_interval = timedelta(minutes=30)
    service_duration = timedelta(minutes=service.duration_minutes)
    
    # Convert rule start/end times to datetimes for easier calendar math
    base_datetime = datetime.combine(target_date, time.min)
    start_dt = datetime.combine(target_date, rule.start_time)
    end_dt = datetime.combine(target_date, rule.end_time)
    
    # 4. Fetch existing non-canceled bookings for this provider on this day
    existing_bookings = Booking.objects.filter(
        provider=provider,
        start_time__date=target_date
    ).exclude(status='Canceled')
    
    available_slots = []
    current_dt = start_dt
    
    # Loop through the day's shift
    while current_dt + service_duration <= end_dt:
        potential_start = current_dt
        potential_end = current_dt + service_duration
        
        # Check if this potential slot overlaps with any existing booking
        is_overlapping = False
        for booking in existing_bookings:
            # Convert timezone-aware datetimes to naive for comparison
            b_start = booking.start_time.replace(tzinfo=None)
            b_end = booking.end_time.replace(tzinfo=None)
            
            # Standard overlap formula: (StartA < EndB) and (EndA > StartB)
            if potential_start < b_end and potential_end > b_start:
                is_overlapping = True
                break
        
        # Also prevent booking past times if the target date is today
        if target_date == date.today() and potential_start < datetime.now():
            is_overlapping = True
            
        if not is_overlapping:
            available_slots.append(potential_start.time())
            
        current_dt += slot_interval # Move to next 30-minute interval
        
    return available_slots