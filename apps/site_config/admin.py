from django import forms
from django.contrib import admin
from django.db import models
from django_summernote.widgets import SummernoteWidget
from solo.admin import SingletonModelAdmin

from .email_service import EMAIL_PLACEHOLDERS, find_unknown_placeholders
from .models import (
    Announcement,
    AnnouncementTranslation,
    ContentBlock,
    ContentBlockTranslation,
    EmailTemplate,
    EmailTemplateTranslation,
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


# ── Email Templates (Phase 7C) ────────────────────────────────

class EmailTemplateTranslationForm(forms.ModelForm):
    """Validates {{ placeholder }} syntax on save.

    Blocks saving when unknown placeholders are found, listing valid ones.
    This prevents silent broken emails from typos like {{ clietn_name }}.
    """

    class Meta:
        model = EmailTemplateTranslation
        fields = '__all__'

    def _validate_placeholders(self, field_name, value):
        if not value:
            return
        unknown = find_unknown_placeholders(value)
        if unknown:
            valid = ', '.join(sorted(EMAIL_PLACEHOLDERS.keys()))
            raise forms.ValidationError(
                f"Unknown placeholder(s) in {field_name}: "
                f"{', '.join(unknown)}. "
                f"Valid placeholders are: {valid}"
            )

    def clean_subject(self):
        self._validate_placeholders('subject', self.cleaned_data.get('subject', ''))
        return self.cleaned_data.get('subject', '')

    def clean_body_text(self):
        self._validate_placeholders('body_text', self.cleaned_data.get('body_text', ''))
        return self.cleaned_data.get('body_text', '')

    def clean_body_html(self):
        self._validate_placeholders('body_html', self.cleaned_data.get('body_html', ''))
        return self.cleaned_data.get('body_html', '')


class EmailTemplateTranslationInline(admin.StackedInline):
    model = EmailTemplateTranslation
    extra = 3  # one row per language (hu/en/de)
    form = EmailTemplateTranslationForm


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('email_type', 'is_active', 'translation_count')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('email_type',)
    inlines = [EmailTemplateTranslationInline]

    def translation_count(self, obj):
        return obj.translations.count()
    translation_count.short_description = "Translations"

    def get_readonly_fields(self, request, obj=None):
        """email_type is set at creation, locked after."""
        if obj:
            return ('email_type',)
        return ()

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Pass available placeholders to the template for inline help text."""
        extra_context = extra_context or {}
        extra_context['placeholder_help'] = EMAIL_PLACEHOLDERS
        return super().changeform_view(request, object_id, form_url, extra_context)
