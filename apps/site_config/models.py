from django.db import models
from solo.models import SingletonModel

class SiteConfiguration(SingletonModel):
    # Hero Section
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

    # Footer Contact Info
    salon_address = models.CharField(max_length=255, blank=True)
    salon_phone = models.CharField(max_length=20, blank=True)
    salon_email = models.EmailField(blank=True)

    # Footer Social Media Links
    social_instagram = models.URLField(blank=True, help_text="Full URL to your Instagram profile.")
    social_facebook = models.URLField(blank=True, help_text="Full URL to your Facebook page.")
    social_tiktok = models.URLField(blank=True, help_text="Full URL to your TikTok profile.")

    class Meta:
        verbose_name = "Site Configuration"

    def __str__(self):
        return "Site Configuration"