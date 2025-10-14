from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Provider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional link to a user account for future provider dashboard."
    )
    display_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    # profile_image_url will be handled by an ImageField in a later step

    class Meta:
        verbose_name = "Provider"
        verbose_name_plural = "Providers"

    def __str__(self):
        return self.display_name

class AvailabilityRule(models.Model):
    """
    Represents a recurring weekly availability rule for a provider.
    e.g., 'Provider A is available every Monday from 09:00 to 17:00'.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='availability_rules')
    day_of_week = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0=Monday, 1=Tuesday, ..., 6=Sunday"
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = "Availability Rule"
        verbose_name_plural = "Availability Rules"
        ordering = ['provider', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.provider.display_name} - Day {self.day_of_week}: {self.start_time}-{self.end_time}"

class TimeSlotOverride(models.Model):
    """
    Represents an exception to the regular availability rules.
    Used for one-off events like holidays, vacations, or special hours.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='overrides')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_available = models.BooleanField(default=False, help_text="Check if this is a special opening, uncheck for a day off.")

    class Meta:
        verbose_name = "Time Slot Override"
        verbose_name_plural = "Time Slot Overrides"
        ordering = ['start_datetime']

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.provider.display_name} - {self.start_datetime} to {self.end_datetime} ({status})"