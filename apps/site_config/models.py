from django.db import models
from solo.models import SingletonModel

class SiteConfiguration(SingletonModel):
    hero_title = models.CharField(
        max_length=200, 
        default="Authentic African Braiding in the Heart of Budapest"
    )
    hero_subtitle = models.TextField(
        blank=True, 
        default="Experience timeless beauty and intricate designs, handcrafted with passion and tradition."
    )
    hero_image = models.ImageField(
        upload_to='hero/', 
        blank=True, 
        null=True, 
        help_text="Upload the main background image for the homepage hero section."
    )

    class Meta:
        verbose_name = "Site Configuration"

    def __str__(self):
        return "Site Configuration"