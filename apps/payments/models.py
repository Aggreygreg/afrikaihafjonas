from django.db import models
from apps.bookings.models import Booking

class Payment(models.Model):
    """
    Records a financial transaction associated with a booking.
    """
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    gateway = models.CharField(max_length=50, help_text="e.g., Stripe, PayPal, Cash")
    gateway_transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment of {self.amount} for Booking {self.booking.booking_code}"