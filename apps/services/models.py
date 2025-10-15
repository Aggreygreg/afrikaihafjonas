from django.db import models
from apps.providers.models import Provider

class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration of the service in minutes."
    )
    providers = models.ManyToManyField(
        Provider,
        related_name="services",
        blank=True,
        help_text="Providers who can perform this service."
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