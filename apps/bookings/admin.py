from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_code',
        'service',
        'client',
        'provider',
        'start_time',
        'status',
    )
    list_filter = ('status', 'provider', 'start_time')
    search_fields = (
        'client__username',
        'provider__display_name',
        'service__title',
        'booking_code',
    )
    readonly_fields = ('booking_code', 'created_at')