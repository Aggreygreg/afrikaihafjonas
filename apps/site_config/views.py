from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import get_language

from .constants import LanguageChoices
from .models import FAQ, FAQTopic

# Static site-level pages (About, Contact, Terms, Privacy).
#
# These pages are intentionally "fat models, skinny templates": the salon
# contact details live on the SiteConfiguration singleton, which is injected
# into every template via the `apps.site_config.context_processors.site_config`
# context processor as `{{ config.* }}`. The views therefore stay thin — they
# simply select the template to render.


def about_page(request):
    """Salon story, mission, team and membership badges."""
    return render(request, "pages/about.html")


def contact_page(request):
    """Salon address, phone, email, business hours, social links and map."""
    return render(request, "pages/contact.html")


def terms_page(request):
    """Terms & Conditions: deposit/hold, appointment request, photos, cancellation."""
    return render(request, "pages/terms.html")


def privacy_page(request):
    """GDPR-compliant Privacy Policy."""
    return render(request, "pages/privacy.html")


def _active_language():
    """Return the current 2-letter language code, defaulting to HU (base)."""
    lang = get_language() or LanguageChoices.HU
    return lang[:2]


def _resolve_faq_entries(faqs):
    """Resolve FAQs to (translation, faq) pairs for the active language.

    Falls back to the base language (HU); FAQs with no usable translation
    are skipped — same policy as the ``get_faqs`` template tag.
    """
    lang = _active_language()
    entries = []
    for faq in faqs:
        trans = (
            faq.translations.filter(language=lang).first()
            or faq.translations.filter(language=LanguageChoices.HU).first()
        )
        if trans:
            entries.append((trans, faq))
    return entries


def faq_page(request):
    """Public FAQ: admin-managed topics + entries, live search, grouped display.

    Behavior (Phase 7 multilingual parent/translation architecture):
    - Active topics render in ``display_order``; each shows its active FAQs.
    - FAQs without a topic (or whose topic was deleted) render under
      a translatable "General" section, last.
    - FAQs under an *inactive* topic are hidden (the admin disabled the group).
    - Search matches the question text and the tag-stripped answer text of
      the *resolved* translation, case-insensitively.
    - HTMX requests (live search) receive the accordion partial only;
      a plain GET renders the full page (native/no-JS fallback).
    """
    lang = _active_language()
    query = (request.GET.get("q") or "").strip()

    active_topics = list(
        FAQTopic.objects.filter(is_active=True).order_by("display_order", "pk")
    )
    active_topic_ids = {topic.pk for topic in active_topics}

    faqs = (
        FAQ.objects.filter(is_active=True)
        .select_related("topic")
        .order_by("display_order", "pk")
    )
    entries = _resolve_faq_entries(faqs)

    # Hide FAQs grouped under inactive topics; keep ungrouped ones.
    entries = [
        (trans, faq)
        for trans, faq in entries
        if faq.topic_id is None or faq.topic_id in active_topic_ids
    ]

    if query:
        needle = query.lower()
        entries = [
            (trans, faq)
            for trans, faq in entries
            if needle in trans.question.lower()
            or needle in strip_tags(trans.answer).lower()
        ]

    sections = []
    for topic in active_topics:
        items = [(trans, faq) for trans, faq in entries if faq.topic_id == topic.pk]
        if not items:
            continue
        name = (
            topic.translations.filter(language=lang).first()
            or topic.translations.filter(language=LanguageChoices.HU).first()
        )
        if not name:
            # Degenerate admin state (no translation at all): hide the heading,
            # consistent with skipping FAQs that have no translation.
            continue
        sections.append({"name": name.name, "items": items})

    general_items = [(trans, faq) for trans, faq in entries if faq.topic_id is None]
    if general_items:
        sections.append({"name": None, "items": general_items})  # None → "General"

    context = {
        "sections": sections,
        "query": query,
    }

    if request.headers.get("HX-Request"):
        return render(request, "pages/partials/faq_list.html", context)

    return render(request, "pages/faq.html", context)
