from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from apps.bookings.models import Booking

class Review(models.Model):
    """
    Represents a client review for a completed booking.
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="review",
        primary_key=True,
        help_text="Ensures one review per booking."
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(
        default=True,
        help_text="Admins can uncheck this to hide a review."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for Booking {self.booking.booking_code} ({self.rating} stars)"