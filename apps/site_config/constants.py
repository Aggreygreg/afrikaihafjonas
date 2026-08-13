"""
Shared constants used across the entire project.

Importing from here is safe — no model imports, no circular dependencies.
"""
from django.db import models


class LanguageChoices(models.TextChoices):
    """Supported languages for the salon platform.

    'hu' is the base language (LANGUAGE_CODE = 'hu').
    Used by: AppointmentRequest.customer_language,
             all Translation models (FAQ, ContentBlock, etc.),
             EmailTemplateTranslation, SEO translations.
    """
    HU = "hu", "Magyar"
    EN = "en", "English"
    DE = "de", "Deutsch"
