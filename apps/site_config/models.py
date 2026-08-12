import bleach
from django.db import models
from solo.models import SingletonModel

from .constants import LanguageChoices


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


# ── Bleach sanitization (Decision #33) ─────────────────────────
# Strict tag whitelist shared by every WYSIWYG (django-summernote) field.
# Output of ``sanitize_html`` is safe to render in templates with ``|safe``.
ALLOWED_TAGS = ['p', 'strong', 'em', 'h2', 'h3', 'ul', 'ol', 'li', 'a', 'br']
ALLOWED_ATTRIBUTES = {'a': ['href', 'target', 'rel']}


def sanitize_html(raw):
    """Strip every tag/attribute outside the whitelist.

    Applied on save to all WYSIWYG output so the template can render it
    with ``|safe`` without an XSS risk. ``strip=True`` removes disallowed
    tags but keeps their inner text.
    """
    if not raw:
        return ''
    return bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


# ── FAQ (Category B — parent + translations) ───────────────────
class FAQ(models.Model):
    """Parent FAQ record. Orderable, toggleable; text lives in translations."""

    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        # Prefer the base-language (HU) question for a readable admin label.
        trans = self.translations.filter(language=LanguageChoices.HU).first()
        return trans.question if trans else f"FAQ #{self.pk}"


class FAQTranslation(models.Model):
    """One translation per language for a FAQ."""

    faq = models.ForeignKey(FAQ, related_name='translations', on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    question = models.CharField(max_length=300)
    answer = models.TextField(
        help_text="WYSIWYG HTML. Sanitized on save with bleach (strict tag whitelist)."
    )

    class Meta:
        unique_together = ('faq', 'language')
        verbose_name = "FAQ translation"
        verbose_name_plural = "FAQ translations"

    def __str__(self):
        return f"{self.get_language_display()} — {self.question[:60]}"

    def save(self, *args, **kwargs):
        self.answer = sanitize_html(self.answer)
        super().save(*args, **kwargs)


# ── ContentBlock (Category B — identified by slug) ─────────────
class ContentBlock(models.Model):
    """Reusable prose block identified by slug (e.g. 'about_page', 'terms_page')."""

    slug = models.SlugField(max_length=100, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = "Content block"
        verbose_name_plural = "Content blocks"

    def __str__(self):
        return self.slug


class ContentBlockTranslation(models.Model):
    """One translation per language for a ContentBlock."""

    content_block = models.ForeignKey(
        ContentBlock, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(
        help_text="WYSIWYG HTML. Sanitized on save with bleach (strict tag whitelist)."
    )

    class Meta:
        unique_together = ('content_block', 'language')
        verbose_name = "Content block translation"
        verbose_name_plural = "Content block translations"

    def __str__(self):
        return f"{self.content_block.slug} ({self.get_language_display()})"

    def save(self, *args, **kwargs):
        self.body = sanitize_html(self.body)
        super().save(*args, **kwargs)


# ── Announcement / Banner (Category B) ─────────────────────────
class Announcement(models.Model):
    """Site-wide banner. Admin controls message, scheduling and dismissibility."""

    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return self.slug


class AnnouncementTranslation(models.Model):
    """One translation per language for an Announcement."""

    announcement = models.ForeignKey(
        Announcement, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    message = models.CharField(max_length=500)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('announcement', 'language')
        verbose_name = "Announcement translation"
        verbose_name_plural = "Announcement translations"

    def __str__(self):
        return f"{self.announcement.slug} ({self.get_language_display()})"


# ──────────────────────────────────────────────────────────────
# Phase 7C — Email Templates (Category B: admin-managed, multilingual)
# ──────────────────────────────────────────────────────────────


class EmailTemplate(models.Model):
    """Parent: defines an email type and its active state.

    EMAIL_TYPES is a developer-controlled enum — NOT admin-extensible.
    Adding a new email type requires code changes (new trigger logic).
    The admin controls the subject/body content via EmailTemplateTranslation.
    """

    EMAIL_TYPES = [
        ('request_received', 'Request Received'),
        ('verification_pending', 'Payment Verification Pending'),
        ('payment_verified', 'Payment Verified'),
        ('appointment_approved', 'Appointment Approved'),
        ('appointment_rejected', 'Appointment Rejected'),
        ('appointment_expired', 'Appointment Expired'),
        ('expiry_reminder', 'Expiry Reminder'),
        ('refund_notification', 'Refund Notification'),
    ]

    email_type = models.CharField(
        max_length=50, choices=EMAIL_TYPES, unique=True,
        help_text="Developer-controlled identifier. Adding new types requires code changes.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If unchecked, no email will be sent for this type.",
    )

    class Meta:
        verbose_name = "Email template"
        verbose_name_plural = "Email templates"

    def __str__(self):
        return self.get_email_type_display()


class EmailTemplateTranslation(models.Model):
    """One translation per language for an EmailTemplate.

    Provides subject + body_text + optional body_html.
    No WYSIWYG — email HTML is fragile, plain text is primary.
    """

    template = models.ForeignKey(
        EmailTemplate, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    subject = models.CharField(max_length=200)
    body_text = models.TextField(
        help_text="Plain text body. Use {{ placeholders }}. "
                  "No WYSIWYG — email plain text is the primary format.",
    )
    body_html = models.TextField(
        blank=True,
        help_text="Optional HTML body. Plain HTML textarea only (no WYSIWYG). "
                  "Email HTML is fragile — use simple inline styles only.",
    )

    class Meta:
        unique_together = ('template', 'language')
        verbose_name = "Email template translation"
        verbose_name_plural = "Email template translations"

    def __str__(self):
        return f"{self.template.get_email_type_display()} ({self.get_language_display()})"
