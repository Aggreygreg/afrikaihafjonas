import uuid
from django.db import models
from django.conf import settings
from apps.providers.models import Provider
from apps.services.models import Service

class Booking(models.Model):
    """
    Represents a scheduled appointment.
    """
    class BookingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Confirmation"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    booking_code = models.CharField(max_length=8, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-start_time']

    def __str__(self):
        return f"Booking for {self.service.title} with {self.provider.display_name} on {self.start_time.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        if not self.booking_code:
            # Generate a unique 8-character code
            self.booking_code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)