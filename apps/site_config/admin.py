from django.contrib import admin
from django.db import models
from django_summernote.widgets import SummernoteWidget
from solo.admin import SingletonModelAdmin

from .models import (
    Announcement,
    AnnouncementTranslation,
    ContentBlock,
    ContentBlockTranslation,
    FAQ,
    FAQTranslation,
    SiteConfiguration,
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Branding', {
            'fields': ('business_name', 'logo', 'favicon'),
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_image'),
        }),
        ('Contact Info', {
            'fields': ('salon_address', 'address_description', 'salon_phone', 'salon_email'),
        }),
        ('Business Hours', {
            'fields': ('business_hours',),
        }),
        ('Location & Web', {
            'fields': ('google_maps_link', 'website_url'),
        }),
        ('Social Media', {
            'fields': ('social_instagram', 'social_facebook', 'social_tiktok'),
        }),
    )


# ── Shared inline config ───────────────────────────────────────
# django-summernote's `summernote_fields` only targets the ModelAdmin's own
# fields — it does NOT reach into inline fields. For WYSIWYG inside inlines we
# override the widget on TextField, which is exactly the answer/body fields.
SUMMERNOTE_OVERRIDES = {
    models.TextField: {'widget': SummernoteWidget()},
}


# ── FAQ ────────────────────────────────────────────────────────
class FAQTranslationInline(admin.StackedInline):
    model = FAQTranslation
    extra = 3  # one row per language (hu/en/de)
    formfield_overrides = SUMMERNOTE_OVERRIDES


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_display_links = ('__str__',)
    list_filter = ('is_active',)
    search_fields = ('translations__question',)
    inlines = [FAQTranslationInline]


# ── ContentBlock ───────────────────────────────────────────────
class ContentBlockTranslationInline(admin.StackedInline):
    model = ContentBlockTranslation
    extra = 3
    formfield_overrides = SUMMERNOTE_OVERRIDES


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('slug', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_display_links = ('slug',)
    list_filter = ('is_active',)
    search_fields = ('slug', 'translations__title', 'translations__body')
    inlines = [ContentBlockTranslationInline]


# ── Announcement ───────────────────────────────────────────────
class AnnouncementTranslationInline(admin.StackedInline):
    model = AnnouncementTranslation
    extra = 3  # message is a CharField (plain text) — no WYSIWYG needed


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('slug', 'display_order', 'is_active', 'is_dismissible',
                    'starts_at', 'ends_at')
    list_editable = ('display_order', 'is_active', 'is_dismissible')
    list_display_links = ('slug',)
    list_filter = ('is_active',)
    search_fields = ('slug', 'translations__message')
    inlines = [AnnouncementTranslationInline]
