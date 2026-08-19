"""Template tags for customer-facing, multilingual content (Phase 7D).

These tags resolve the active language and return the matching translation,
falling back to the base language (HU) when the requested translation is
missing. ContentBlock/FAQ bodies are pre-sanitized by bleach on save, so they
are rendered in templates with ``|safe``.
"""
from django import template
from django.db import models
from django.utils import timezone
from django.utils.translation import get_language

from apps.site_config.constants import LanguageChoices
from apps.site_config.models import (
    Announcement,
    ContentBlock,
    ContentBlockTranslation,
    FAQ,
    FAQTranslation,
)

register = template.Library()

# The base language is always available as a safe fallback.
BASE_LANGUAGE = LanguageChoices.HU


def _active_language():
    """Return the current 2-letter language code, defaulting to HU."""
    lang = get_language() or BASE_LANGUAGE
    return lang[:2]


@register.simple_tag
def get_content_block(slug):
    """Return the ContentBlockTranslation for the active language.

    Resolution order:
      1. The active language (e.g. ``en`` / ``de``).
      2. The base language (``hu``) as a guaranteed fallback.
      3. ``None`` if the ContentBlock does not exist at all.

    Usage::

        {% load content_tags %}
        {% get_content_block 'about_page' as block %}
        {% if block %}
          <h1>{{ block.title }}</h1>
          <div class="prose">{{ block.body|safe }}</div>
        {% endif %}
    """
    try:
        block = ContentBlock.objects.get(slug=slug, is_active=True)
    except ContentBlock.DoesNotExist:
        return None

    lang = _active_language()
    try:
        return block.translations.get(language=lang)
    except ContentBlockTranslation.DoesNotExist:
        try:
            return block.translations.get(language=BASE_LANGUAGE)
        except ContentBlockTranslation.DoesNotExist:
            return None


@register.simple_tag
def get_faqs():
    """Return active FAQ translations, ordered, for the active language.

    Each FAQ is resolved to its active-language translation, falling back to
    the base language (HU). FAQs with no usable translation are skipped.
    """
    lang = _active_language()
    faqs = FAQ.objects.filter(is_active=True).order_by('display_order')
    result = []
    for faq in faqs:
        trans = (
            faq.translations.filter(language=lang).first()
            or faq.translations.filter(language=BASE_LANGUAGE).first()
        )
        if trans:
            result.append(trans)
    return result


@register.simple_tag
def get_active_announcements():
    """Return announcement translations for the active, in-window banners.

    Filters: ``is_active``, plus the optional scheduling window
    (``starts_at`` null-or-past, ``ends_at`` null-or-future), ordered by
    ``display_order``. Each announcement resolves to its active-language
    translation with HU fallback; untranslated announcements are skipped.

    Returns the *translation* rows (``{{ a.message }}``, ``{{ a.link_url }}``,
    ``{{ a.link_text }}``); the parent record (slug, ``is_dismissible``) is
    reachable via ``{{ a.announcement.* }}``.
    """
    now = timezone.now()
    banners = (
        Announcement.objects.filter(is_active=True)
        .filter(models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now))
        .filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
        .order_by('display_order', 'pk')
    )
    lang = _active_language()
    result = []
    for banner in banners:
        trans = (
            banner.translations.filter(language=lang).first()
            or banner.translations.filter(language=BASE_LANGUAGE).first()
        )
        if trans:
            result.append(trans)
    return result
