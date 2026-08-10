from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.providers.models import Provider


class ParentCategory(models.Model):
    name = models.CharField(
        max_length=100, unique=True,
        help_text="e.g., 'Women's Braids', 'Men's Braids', 'Children's Braids'",
    )

    class Meta:
        verbose_name = "Parent Category"
        verbose_name_plural = "Parent Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    parent = models.ForeignKey(
        ParentCategory, on_delete=models.CASCADE,
        related_name="subcategories", null=True,
    )
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ["parent", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    # ── Suitability & Age Fields ───────────────────────────────
    TARGET_AUDIENCE_CHOICES = [
        ("Adults", "Adults (16+)"),
        ("Children", "Children (8-15)"),
        ("Everyone", "Everyone (8+)"),
    ]
    target_audience = models.CharField(
        max_length=50, choices=TARGET_AUDIENCE_CHOICES,
        default="Adults",
        help_text="Defines the strict age policy for this service.",
    )
    best_for_hair_types = models.CharField(
        max_length=255, blank=True,
        help_text="e.g., 'Medium Hair, Thick Hair'",
    )
    suitability_warning = models.TextField(
        blank=True,
        help_text="e.g., 'This hairstyle may place additional tension on very thin hair.'",
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
        ordering = ["title"]

    def __str__(self):
        return self.title

    # ── Fat Model Properties (Skinny Templates) ────────────────
    @property
    def formatted_duration(self):
        """Convert minutes to human-readable string: '2 hrs 30 mins'."""
        hours, mins = divmod(self.duration_minutes, 60)
        if hours and mins:
            return f"{hours} hr{'s' if hours > 1 else ''} {mins} min{'s' if mins > 1 else ''}"
        elif hours:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{mins} mins"

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
        return f"Image {self.order} for {self.service.title}"

    @property
    def linked_options_json(self):
        """Returns a list of option IDs for frontend JS image matching."""
        return list(self.linked_options.values_list("id", flat=True))


class ServiceOption(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="options",
    )
    group_name = models.CharField(
        max_length=100, help_text="e.g., 'Color', 'Length', 'Add-on'",
    )
    value = models.CharField(
        max_length=100, help_text="e.g., 'Black', '16 inches', 'Deep Conditioning'",
    )
    additional_price = models.DecimalField(
        max_digits=8, decimal_places=0, default=0,
        help_text="Added to base price.",
    )

    class Meta:
        verbose_name = "Service Option"
        verbose_name_plural = "Service Options"
        ordering = ["group_name", "value"]

    def __str__(self):
        return f"{self.group_name}: {self.value} (+{self.additional_price} Ft)"
