from django.db import models
from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    """Singleton — all customer-facing business information in one place.

    Operational data (phone, email, address) is single-language.
    For per-language prose (directions, hours descriptions), use ContentBlocks
    (Phase 7D) keyed by slug — not this model.
    """

    # ── Branding ───────────────────────────────────────────────
    business_name = models.CharField(
        max_length=200, default="Afrikai Hajfonás",
        help_text="The salon's business name, shown in the header, footer, and emails.",
    )
    logo = models.ImageField(
        upload_to='branding/', blank=True, null=True,
        help_text="Site logo. Recommended: transparent PNG, max height 48px.",
    )
    favicon = models.ImageField(
        upload_to='branding/', blank=True, null=True,
        help_text="Favicon (browser tab icon). Recommended: 32×32 or 64×64 PNG/ICO.",
    )

    # ── Hero Section ───────────────────────────────────────────
    hero_title = models.CharField(
        max_length=200,
        default="Authentic African Braiding in the Heart of Budapest"
    )
    hero_subtitle = models.TextField(
        blank=True,
        default="Experience timeless beauty and intricate designs, handcrafted with passion and tradition."
    )
    hero_image = models.ImageField(
        upload_to='hero/', blank=True, null=True,
        help_text="Upload the main background image for the homepage hero section."
    )

    # ── Contact Info ───────────────────────────────────────────
    salon_address = models.CharField(max_length=255, blank=True)
    address_description = models.TextField(
        blank=True,
        help_text="Directions / landmark description to help customers find the salon.",
    )
    salon_phone = models.CharField(max_length=20, blank=True)
    salon_email = models.EmailField(blank=True)

    # ── Business Hours ─────────────────────────────────────────
    business_hours = models.TextField(
        blank=True,
        help_text="Operating hours. Plain text, e.g., 'Mon–Fri: 9:00–18:00, Sat: 10:00–16:00'.",
    )

    # ── Location & Web ─────────────────────────────────────────
    google_maps_link = models.URLField(
        blank=True,
        help_text="Full Google Maps URL for the salon's location.",
    )
    website_url = models.URLField(
        blank=True,
        help_text="Canonical website URL (used for SEO canonical tags and email links).",
    )

    # ── Social Media Links ─────────────────────────────────────
    social_instagram = models.URLField(blank=True, help_text="Full URL to your Instagram profile.")
    social_facebook = models.URLField(blank=True, help_text="Full URL to your Facebook page.")
    social_tiktok = models.URLField(blank=True, help_text="Full URL to your TikTok profile.")

    class Meta:
        verbose_name = "Site Configuration"

    def __str__(self):
        return "Site Configuration"
