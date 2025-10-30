from django.db import models
from apps.providers.models import Provider

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=8, decimal_places=0)
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration of the service in minutes."
    )
    providers = models.ManyToManyField(
        Provider,
        related_name="services",
        blank=True,
        help_text="Providers who can perform this service."
    )
    
    # New fields
    video_url = models.URLField(
        blank=True,
        help_text="Optional: A link to a TikTok, Instagram, or Google Drive video."
    )
    is_popular = models.BooleanField(
        default=False,
        help_text="Check this to feature the service on the homepage."
    )

    # Per-service payment options
    allow_full_payment = models.BooleanField(default=True)
    allow_deposit_payment = models.BooleanField(default=True)
    allow_pay_later = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['title']

    def __str__(self):
        return self.title

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='service_images/')
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Images will be sorted by this number (0 is first)."
    )

    class Meta:
        verbose_name = "Service Image"
        verbose_name_plural = "Service Images"
        ordering = ['order']

class ServiceOption(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='options')
    group_name = models.CharField(
        max_length=100,
        help_text="e.g., 'Color', 'Length', 'Add-on'"
    )
    value = models.CharField(
        max_length=100,
        help_text="e.g., 'Black', '16 inches', 'Deep Conditioning'"
    )
    additional_price = models.DecimalField(
        max_digits=8,
        decimal_places=0,
        default=0,
        help_text="Added to the base price if this option is selected."
    )

    class Meta:
        verbose_name = "Service Option"
        verbose_name_plural = "Service Options"
        ordering = ['group_name', 'value']

    def __str__(self):
        return f"{self.group_name}: {self.value} (+{self.additional_price} Ft)"