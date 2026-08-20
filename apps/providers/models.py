from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import get_language

from apps.site_config.constants import LanguageChoices


def _active_lang():
    """Return the current 2-letter language code, defaulting to HU (base)."""
    lang = get_language() or LanguageChoices.HU
    return lang[:2]


class Provider(models.Model):
    """Stylist profile.

    Structural fields only (display_name, user, profile_image). The
    customer-facing bio lives in ProviderTranslation (HU/EN/DE) — Category B,
    consistent with all other admin-managed multilingual content
    (ARCHITECTURAL_PRINCIPLES.md §4).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional link to a user account for future provider dashboard."
    )
    display_name = models.CharField(max_length=100)
    profile_image = models.ImageField(
        upload_to='provider_images/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Provider"
        verbose_name_plural = "Providers"

    def __str__(self):
        return self.display_name

    def get_translation(self, lang=None):
        """Return the best available translation for the active language."""
        lang = lang or _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
            or self.translations.first()
        )

    @property
    def display_bio(self):
        """Return the bio in the active language, falling back to HU."""
        trans = self.get_translation()
        return trans.bio if trans else ""


class ProviderTranslation(models.Model):
    """One per language for a Provider's bio (Category B — parent+Translation)."""
    provider = models.ForeignKey(
        Provider, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    bio = models.TextField(blank=True, help_text="Stylist bio in this language.")

    class Meta:
        unique_together = ('provider', 'language')
        verbose_name = "Provider translation"
        verbose_name_plural = "Provider translations"

    def __str__(self):
        return f"{self.provider.display_name} — {self.get_language_display()}"


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