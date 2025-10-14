from django.db import models
from django.conf import settings

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