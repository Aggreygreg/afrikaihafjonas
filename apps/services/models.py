from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import get_language, gettext_lazy as _, ngettext
from apps.providers.models import Provider
from apps.site_config.constants import LanguageChoices


# ── Helper: active-language code (HU fallback) ─────────────────

def _active_lang():
    """Return the current 2-letter language code, defaulting to HU (base)."""
    lang = get_language() or LanguageChoices.HU
    return lang[:2]


# ── Catalog Models ─────────────────────────────────────────────

class ParentCategory(models.Model):
    """Top-level category tab on the catalog page (e.g. Women's Braids).

    Decision #38: ``name`` is no longer on this model — it lives in
    ParentCategoryTranslation (HU/EN/DE).  The admin creates the parent
    and supplies translations via the inline admin.
    """

    class Meta:
        verbose_name = "Parent Category"
        verbose_name_plural = "Parent Categories"
        ordering = ["pk"]  # creation order — preserves seeded tab order

    def __str__(self):
        trans = self.translations.filter(language=LanguageChoices.HU).first()
        return trans.name if trans else f"Parent Category #{self.pk}"

    def get_translation(self, lang=None):
        """Return the translation for *lang* (or active language), HU fallback."""
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    @property
    def display_name(self):
        """Translated name for the active language (HU fallback)."""
        trans = self.get_translation()
        return trans.name if trans else str(self)


class ServiceCategory(models.Model):
    """Sub-category under a ParentCategory (e.g. Knotless Box Braids).

    Decision #38: ``name`` is in ServiceCategoryTranslation.
    """

    parent = models.ForeignKey(
        ParentCategory, on_delete=models.CASCADE,
        related_name="subcategories", null=True,
    )

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ["parent", "pk"]

    def __str__(self):
        hu_trans = self.translations.filter(language=LanguageChoices.HU).first()
        name = hu_trans.name if hu_trans else f"Subcategory #{self.pk}"
        if self.parent:
            parent_name = self.parent.display_name
            return f"{parent_name} — {name}"
        return name

    def get_translation(self, lang=None):
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    @property
    def display_name(self):
        trans = self.get_translation()
        return trans.name if trans else str(self)


class Service(models.Model):
    """A braiding service with pricing, duration, and multilingual text.

    Decision #38: ``title``, ``description``, ``best_for_hair_types`` and
    ``suitability_warning`` are in ServiceTranslation (HU/EN/DE).
    Operational fields (price, duration, discount, target_audience key)
    remain on this model.
    """

    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    # ── Suitability & Age ────────────────────────────────────────
    TARGET_AUDIENCE_CHOICES = [
        ("Adults", _("Adults (16+)")),
        ("Children", _("Children (8-15)")),
        ("Everyone", _("Everyone (8+)")),
    ]
    target_audience = models.CharField(
        max_length=50, choices=TARGET_AUDIENCE_CHOICES,
        default="Adults",
        help_text="Defines the strict age policy for this service.",
    )

    # ── Pricing & Duration ─────────────────────────────────────
    base_price = models.DecimalField(max_digits=8, decimal_places=0)
    discount_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100. Applied as a seasonal discount (bulk admin action).",
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration of the service in minutes.",
    )

    # ── Relations ──────────────────────────────────────────────
    providers = models.ManyToManyField(
        Provider, related_name="services", blank=True,
        help_text="Providers who can perform this service.",
    )

    # ── Media & Flags ──────────────────────────────────────────
    video_url = models.URLField(
        blank=True,
        help_text="Optional: A link to a TikTok, Instagram, or Google Drive video.",
    )
    is_popular = models.BooleanField(
        default=False,
        help_text="Check this to feature the service on the homepage.",
    )

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["pk"]

    def __str__(self):
        trans = self.translations.filter(language=LanguageChoices.HU).first()
        return trans.title if trans else f"Service #{self.pk}"

    def get_translation(self, lang=None):
        """Return the ServiceTranslation for *lang* (or active), HU fallback."""
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    # ── Translated display properties (skinny templates) ─────────

    @property
    def display_title(self):
        trans = self.get_translation()
        return trans.title if trans else str(self)

    @property
    def display_description(self):
        trans = self.get_translation()
        return trans.description if trans else ""

    @property
    def display_best_for_hair_types(self):
        trans = self.get_translation()
        return trans.best_for_hair_types if trans else ""

    @property
    def display_suitability_warning(self):
        trans = self.get_translation()
        return trans.suitability_warning if trans else ""

    # ── Fat Model Properties (Skinny Templates) ────────────────
    @property
    def formatted_duration(self):
        """Convert minutes to human-readable, translated string."""
        hours, mins = divmod(self.duration_minutes, 60)
        parts = []
        if hours:
            parts.append(ngettext("%(d)d hour", "%(d)d hours", hours) % {"d": hours})
        if mins:
            parts.append(ngettext("%(d)d min", "%(d)d mins", mins) % {"d": mins})
        return " ".join(parts) if parts else _("0 mins")

    @property
    def has_discount(self):
        """True if this service currently has a seasonal discount."""
        return self.discount_percentage > 0

    @property
    def discounted_price(self):
        """Returns the price after discount, or base price if no discount."""
        if self.has_discount:
            from decimal import Decimal
            discount_factor = Decimal(self.discount_percentage) / Decimal(100)
            discount_amount = self.base_price * discount_factor
            return self.base_price - discount_amount
        return self.base_price

    @property
    def formatted_base_price(self):
        """Zero-decimal HUF: '55,000 Ft'."""
        return "{:,} Ft".format(int(self.base_price))

    @property
    def formatted_discounted_price(self):
        """Zero-decimal HUF after discount: '46,750 Ft'."""
        return "{:,} Ft".format(int(self.discounted_price))

    def get_options_grouped(self):
        """Return option groups for the active language, HU fallback.

        Groups are keyed by the HU translation's ``group_name`` (stable across
        languages).  The display ``group_name`` is resolved to the active
        language.  ``is_addon`` detection runs on the HU group name.

        Returns a list of dicts:
        [{"group_name": "Color", "options": [...], "is_addon": False}, ...]
        """
        from collections import OrderedDict

        lang = _active_lang()
        grouped = OrderedDict()
        for opt in self.options.all().prefetch_related(
            "translations"
        ).order_by("pk"):
            hu_trans = opt.translations.filter(language=LanguageChoices.HU).first()
            group_key = hu_trans.group_name if hu_trans else f"Group {opt.pk}"

            if group_key not in grouped:
                is_addon = any(
                    kw in group_key.lower() for kw in ["add", "extra"]
                )
                active_trans = opt.translations.filter(language=lang).first()
                display_name = (
                    active_trans.group_name
                    if active_trans
                    else (hu_trans.group_name if hu_trans else group_key)
                )
                grouped[group_key] = {
                    "group_name": group_key,
                    "display_group_name": display_name,
                    "options": [],
                    "is_addon": is_addon,
                }
            grouped[group_key]["options"].append(opt)
        return list(grouped.values())


class ServiceImage(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="images",
    )
    image = models.ImageField(upload_to="service_images/")
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Images will be sorted by this number (0 is first).",
    )

    # ── SHEIN-Style M2M Matrix ─────────────────────────────────
    linked_options = models.ManyToManyField(
        "ServiceOption", blank=True,
        related_name="images",
        help_text="Select the option(s) this image represents (e.g., 'Black' + 'Waist Length').",
    )

    class Meta:
        verbose_name = "Service Image"
        verbose_name_plural = "Service Images"
        ordering = ["order"]

    def __str__(self):
        return f"Image {self.order} for {self.service.display_title}"

    @property
    def linked_options_json(self):
        """Returns a list of option IDs for frontend JS image matching."""
        return list(self.linked_options.values_list("id", flat=True))


class ServiceOption(models.Model):
    """A selectable option for a service (e.g., Color: Black, Length: Shoulder).

    Decision #38: ``group_name`` remains on this model as a **structural
    grouping key** (used by ``get_options_grouped`` and ``is_addon``
    detection).  It is never shown to customers — the display name comes from
    ServiceOptionTranslation.  ``value`` is removed from this model and lives
    only in translations.
    """
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="options",
    )
    group_name = models.CharField(
        max_length=100,
        help_text="Internal grouping key (e.g., 'Color', 'Length'). "
                  "Never shown to customers — set the display name per language "
                  "in the translations below.",
    )
    additional_price = models.DecimalField(
        max_digits=8, decimal_places=0, default=0,
        help_text="Added to base price.",
    )

    class Meta:
        verbose_name = "Service Option"
        verbose_name_plural = "Service Options"
        ordering = ["group_name", "pk"]

    def __str__(self):
        hu_trans = self.translations.filter(language=LanguageChoices.HU).first()
        if hu_trans:
            return f"{hu_trans.group_name}: {hu_trans.value} (+{self.additional_price} Ft)"
        return f"{self.group_name}: #{self.pk} (+{self.additional_price} Ft)"

    def get_translation(self, lang=None):
        if lang is None:
            lang = _active_lang()
        return (
            self.translations.filter(language=lang).first()
            or self.translations.filter(language=LanguageChoices.HU).first()
        )

    @property
    def display_group_name(self):
        trans = self.get_translation()
        return trans.group_name if trans else self.group_name

    @property
    def display_value(self):
        trans = self.get_translation()
        return trans.value if trans else ""


# ── Translation Models (Category B — parent + translations) ────
# Decision #38: Full customer-facing multilingual support (HU/EN/DE).
# Catalog text (names, titles, descriptions, option labels) now lives in
# Translation records, following the established Phase 7 pattern.

class ParentCategoryTranslation(models.Model):
    """One translation per language for a ParentCategory."""

    parent_category = models.ForeignKey(
        ParentCategory, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('parent_category', 'language')
        verbose_name = "Parent category translation"
        verbose_name_plural = "Parent category translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.name}"


class ServiceCategoryTranslation(models.Model):
    """One translation per language for a ServiceCategory."""

    service_category = models.ForeignKey(
        ServiceCategory, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('service_category', 'language')
        verbose_name = "Service category translation"
        verbose_name_plural = "Service category translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.name}"


class ServiceTranslation(models.Model):
    """One translation per language for a Service.

    Contains all customer-facing text: title, description, suitability
    info (best_for_hair_types), and suitability_warning.
    """

    service = models.ForeignKey(
        Service, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    best_for_hair_types = models.CharField(max_length=255, blank=True)
    suitability_warning = models.TextField(blank=True)

    class Meta:
        unique_together = ('service', 'language')
        verbose_name = "Service translation"
        verbose_name_plural = "Service translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.title[:60]}"


class ServiceOptionTranslation(models.Model):
    """One translation per language for a ServiceOption."""

    service_option = models.ForeignKey(
        ServiceOption, related_name='translations', on_delete=models.CASCADE,
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    group_name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ('service_option', 'language')
        verbose_name = "Service option translation"
        verbose_name_plural = "Service option translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.group_name}: {self.value}"