from django.test import TestCase, override_settings
from django.utils.translation import override

from apps.site_config.constants import LanguageChoices
from apps.site_config.models import (
    Announcement,
    AnnouncementTranslation,
    ContentBlock,
    ContentBlockTranslation,
    FAQ,
    FAQTranslation,
    sanitize_html,
)
from apps.site_config.templatetags.content_tags import (
    get_content_block,
    get_faqs,
)


class SanitizeHtmlTests(TestCase):
    """bleach sanitization helper (Decision #33)."""

    def test_keeps_whitelisted_tags(self):
        raw = "<p>hi <strong>b</strong> <em>i</em></p>"
        self.assertEqual(sanitize_html(raw), raw)

    def test_strips_script_tag(self):
        result = sanitize_html("<p>ok</p><script>alert(1)</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("<p>ok</p>", result)

    def test_strips_disallowed_tags_but_keeps_text(self):
        # <h1> is NOT in the whitelist (only h2/h3); text content survives.
        result = sanitize_html("<h1>Title</h1>")
        self.assertNotIn("<h1>", result)
        self.assertIn("Title", result)

    def test_strips_dangerous_attributes(self):
        result = sanitize_html('<a href="http://x" onclick="evil()">link</a>')
        self.assertNotIn("onclick", result)
        self.assertIn('href="http://x"', result)

    def test_removes_onerror_img_entirely(self):
        result = sanitize_html('<img src=x onerror=alert(1)>')
        self.assertNotIn("<img", result)
        self.assertNotIn("onerror", result)

    def test_empty_and_none_input(self):
        self.assertEqual(sanitize_html(""), "")
        self.assertEqual(sanitize_html(None), "")


class FAQTranslationSaveTests(TestCase):
    """save() must sanitize the WYSIWYG answer field."""

    def test_answer_sanitized_on_create(self):
        faq = FAQ.objects.create(display_order=0)
        trans = FAQTranslation.objects.create(
            faq=faq,
            language=LanguageChoices.HU,
            question="How long do braids last?",
            answer="<p>Weeks.</p><script>x</script>",
        )
        trans.refresh_from_db()
        self.assertNotIn("<script>", trans.answer)
        self.assertIn("<p>Weeks.</p>", trans.answer)

    def test_unique_together_per_language(self):
        faq = FAQ.objects.create()
        FAQTranslation.objects.create(
            faq=faq, language=LanguageChoices.HU, question="Q", answer="A"
        )
        with self.assertRaises(Exception):
            FAQTranslation.objects.create(
                faq=faq, language=LanguageChoices.HU, question="Q2", answer="A2"
            )


class ContentBlockTranslationSaveTests(TestCase):
    """save() must sanitize the WYSIWYG body field."""

    def test_body_sanitized_on_save(self):
        block = ContentBlock.objects.create(slug="unit_test_block")
        trans = ContentBlockTranslation.objects.create(
            content_block=block,
            language=LanguageChoices.HU,
            title="T",
            body="<p>hello</p><iframe src=evil></iframe>",
        )
        trans.refresh_from_db()
        self.assertIn("<p>hello</p>", trans.body)
        self.assertNotIn("<iframe", trans.body)


class AnnouncementModelTests(TestCase):
    def test_can_create_with_translation(self):
        ann = Announcement.objects.create(slug="summer_sale")
        AnnouncementTranslation.objects.create(
            announcement=ann,
            language=LanguageChoices.EN,
            message="20% off this week!",
            link_url="https://example.com",
            link_text="Shop now",
        )
        self.assertEqual(ann.translations.count(), 1)


class SeedMigrationTests(TestCase):
    """The 0005 data migration must seed the static-page ContentBlocks (HU)."""

    def test_static_page_blocks_seeded(self):
        for slug in ("about_page", "terms_page", "privacy_page"):
            self.assertTrue(
                ContentBlock.objects.filter(slug=slug, is_active=True).exists(),
                f"Missing seeded ContentBlock: {slug}",
            )
            block = ContentBlock.objects.get(slug=slug)
            self.assertTrue(
                block.translations.filter(language=LanguageChoices.HU).exists(),
                f"Missing HU translation for {slug}",
            )

    def test_all_blocks_hu_only(self):
        # Phase 7D seeds HU only — EN/DE are added later via the admin.
        for block in ContentBlock.objects.all():
            langs = set(block.translations.values_list("language", flat=True))
            self.assertEqual(langs, {LanguageChoices.HU})


class GetContentBlockTagTests(TestCase):
    def setUp(self):
        # Use a non-seeded slug so we don't collide with the 0005 data migration.
        self.block = ContentBlock.objects.create(slug="test_block", display_order=0)
        ContentBlockTranslation.objects.create(
            content_block=self.block, language=LanguageChoices.HU,
            title="Rolunk", body="<p>HU body</p>",
        )
        ContentBlockTranslation.objects.create(
            content_block=self.block, language=LanguageChoices.EN,
            title="About", body="<p>EN body</p>",
        )

    def test_returns_active_language(self):
        with override("en"):
            trans = get_content_block("test_block")
        self.assertEqual(trans.language, LanguageChoices.EN)
        self.assertIn("EN body", trans.body)

    def test_falls_back_to_hu(self):
        # German has no translation → must fall back to base language (HU).
        with override("de"):
            trans = get_content_block("test_block")
        self.assertEqual(trans.language, LanguageChoices.HU)

    def test_returns_none_for_missing_slug(self):
        self.assertIsNone(get_content_block("does_not_exist"))

    def test_returns_none_for_inactive_block(self):
        self.block.is_active = False
        self.block.save()
        self.assertIsNone(get_content_block("test_block"))


class GetFaqsTagTests(TestCase):
    def setUp(self):
        # Second FAQ created first but should appear after display_order=0.
        self.faq_b = FAQ.objects.create(display_order=1)
        FAQTranslation.objects.create(
            faq=self.faq_b, language=LanguageChoices.HU,
            question="Q-B", answer="A-B",
        )
        self.faq_a = FAQ.objects.create(display_order=0)
        FAQTranslation.objects.create(
            faq=self.faq_a, language=LanguageChoices.HU,
            question="Q-A", answer="A-A",
        )

    def test_ordered_by_display_order(self):
        result = get_faqs()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].question, "Q-A")
        self.assertEqual(result[1].question, "Q-B")

    def test_skips_inactive(self):
        self.faq_a.is_active = False
        self.faq_a.save()
        result = get_faqs()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].question, "Q-B")

    def test_falls_back_to_hu(self):
        with override("en"):
            result = get_faqs()
        # No EN translations exist → every result is the HU fallback.
        self.assertTrue(all(t.language == LanguageChoices.HU for t in result))

    def test_skips_faq_with_no_translation(self):
        FAQ.objects.create(display_order=2)  # no translations at all
        self.assertEqual(len(get_faqs()), 2)


# ──────────────────────────────────────────────────────────────
# Phase 7C — Email Template Tests
# ──────────────────────────────────────────────────────────────

from apps.site_config.email_service import (
    EMAIL_PLACEHOLDERS,
    find_placeholders,
    find_unknown_placeholders,
    render_email,
    render_text,
)
from apps.site_config.models import EmailTemplate, EmailTemplateTranslation


class RenderTextTests(TestCase):
    """Core regex-based placeholder substitution (Decision #33)."""

    def test_basic_substitution(self):
        result = render_text("Hello {{ client_name }}!", {"client_name": "Anna"})
        self.assertEqual(result, "Hello Anna!")

    def test_multiple_placeholders(self):
        result = render_text(
            "{{ client_name }} - {{ payment_reference }}",
            {"client_name": "Anna", "payment_reference": "AFH-123"},
        )
        self.assertEqual(result, "Anna - AFH-123")

    def test_unknown_key_renders_empty(self):
        """Per spec §7.4: unsupported variables render as empty string."""
        result = render_text("Hi {{ client_name }} {{ nonexistent }}!", {"client_name": "X"})
        self.assertEqual(result, "Hi X !")

    def test_missing_from_context_renders_empty(self):
        """A known placeholder missing from context → empty string, no crash."""
        result = render_text("Hi {{ client_name }}", {})
        self.assertEqual(result, "Hi ")

    def test_none_value_renders_empty(self):
        result = render_text("[{{ client_name }}]", {"client_name": None})
        self.assertEqual(result, "[]")

    def test_empty_or_none_text(self):
        self.assertEqual(render_text("", {"x": "y"}), "")
        self.assertEqual(render_text(None, {"x": "y"}), "")

    def test_whitespace_in_placeholder(self):
        """{{  client_name  }} with spaces should still match."""
        result = render_text("Hi {{  client_name  }}", {"client_name": "X"})
        self.assertEqual(result, "Hi X")

    def test_template_tag_injection_blocked(self):
        """Django template tags must NOT be processed — they pass through as-is."""
        result = render_text("{% load admin_list %}{{ client_name }}", {"client_name": "X"})
        self.assertIn("{% load admin_list %}", result)
        self.assertIn("X", result)


class FindUnknownPlaceholdersTests(TestCase):
    def test_detects_typo(self):
        unknown = find_unknown_placeholders("Hi {{ client_nam }}")
        self.assertIn("client_nam", unknown)

    def test_valid_placeholders_not_flagged(self):
        unknown = find_unknown_placeholders("Hi {{ client_name }} {{ payment_reference }}")
        self.assertEqual(unknown, [])

    def test_mixed_valid_and_invalid(self):
        unknown = find_unknown_placeholders("{{ client_name }} {{ typo_key }} {{ hours }}")
        self.assertEqual(unknown, ["typo_key"])

    def test_empty_text(self):
        self.assertEqual(find_unknown_placeholders(""), [])
        self.assertEqual(find_unknown_placeholders(None), [])

    def test_find_all_placeholders(self):
        found = find_placeholders("{{ a }} {{ b }} {{ a }}")
        self.assertEqual(found, {"a", "b"})


class RenderEmailTests(TestCase):
    """Full render_email() integration with DB templates."""

    def test_renders_expiry_reminder_en(self):
        ctx = {
            "hours": 2,
            "payment_reference": "AFH-TEST1",
            "client_name": "Test Client",
            "service_name": "Box Braids",
            "provider_name": "Anna",
            "appointment_date": "2026-08-15",
            "appointment_time": "14:00",
            "appointment_status": "Pending Verification",
            "held_until": "2026-08-12 20:00",
            "admin_url": "http://example.com/admin/1/",
            "salon_name": "Afrikai Hajfonás",
        }
        result = render_email("expiry_reminder", ctx, language="en")
        self.assertIsNotNone(result)
        subject, body_text, body_html = result
        self.assertIn("AFH-TEST1", subject)
        self.assertIn("Test Client", body_text)
        self.assertIn("http://example.com/admin/1/", body_text)

    def test_renders_hu_default_language(self):
        """When language='hu', should get the HU translation."""
        result = render_email("request_received", {"client_name": "T"}, language="hu")
        self.assertIsNotNone(result)
        self.assertIn("T", result[1])  # body_text contains the name

    def test_falls_back_to_hu_when_translation_missing(self):
        """DE translation missing for a custom template → HU fallback."""
        template = EmailTemplate.objects.get(email_type="request_received")
        template.translations.filter(language="de").delete()

        ctx = {"client_name": "Max", "payment_reference": "AFH-X"}
        result = render_email("request_received", ctx, language="de")
        self.assertIsNotNone(result)
        # HU body should contain "Kedves" (Hungarian greeting)
        self.assertIn("Kedves", result[1])

    def test_returns_none_for_unknown_email_type(self):
        result = render_email("nonexistent_type", {}, language="hu")
        self.assertIsNone(result)

    def test_returns_none_for_inactive_template(self):
        template = EmailTemplate.objects.get(email_type="refund_notification")
        template.is_active = False
        template.save()
        result = render_email("refund_notification", {}, language="hu")
        self.assertIsNone(result)

    def test_returns_none_when_no_translations_at_all(self):
        """Template exists but has zero translations → None."""
        EmailTemplate.objects.filter(email_type="payment_verified").delete()
        # Re-create empty parent
        EmailTemplate.objects.create(email_type="payment_verified", is_active=True)
        result = render_email("payment_verified", {}, language="hu")
        self.assertIsNone(result)

    def test_unsupported_placeholder_renders_empty(self):
        """Runtime: unsupported placeholder → empty string (no crash)."""
        # Context deliberately omits 'salon_name' — should render empty
        result = render_email("expiry_reminder", {"hours": 1}, language="en")
        self.assertIsNotNone(result)
        # Subject template has {{ salon_name }} — should render as empty
        self.assertNotIn("{{ ", result[0])


class SeedMigrationTestsEmail(TestCase):
    """Verify the 0007 seed migration created all expected records."""

    def test_eight_template_types_seeded(self):
        expected = {
            "request_received", "verification_pending", "payment_verified",
            "appointment_approved", "appointment_rejected", "appointment_expired",
            "expiry_reminder", "refund_notification",
        }
        actual = set(EmailTemplate.objects.values_list("email_type", flat=True))
        self.assertEqual(actual, expected)

    def test_twenty_four_translations_seeded(self):
        self.assertEqual(EmailTemplateTranslation.objects.count(), 24)

    def test_every_template_has_hu_translation(self):
        for template in EmailTemplate.objects.all():
            self.assertTrue(
                template.translations.filter(language="hu").exists(),
                f"Missing HU translation for {template.email_type}",
            )

    def test_every_template_has_en_de(self):
        for template in EmailTemplate.objects.all():
            for lang in ("en", "de"):
                self.assertTrue(
                    template.translations.filter(language=lang).exists(),
                    f"Missing {lang} translation for {template.email_type}",
                )

    def test_all_templates_active_by_default(self):
        self.assertTrue(EmailTemplate.objects.filter(is_active=True).count(), 8)
        self.assertEqual(EmailTemplate.objects.filter(is_active=False).count(), 0)

    def test_seeded_templates_use_only_known_placeholders(self):
        """No seeded template body should contain unknown placeholders."""
        for trans in EmailTemplateTranslation.objects.all():
            for field_name in ("subject", "body_text"):
                value = getattr(trans, field_name)
                unknown = find_unknown_placeholders(value)
                self.assertEqual(
                    unknown, [],
                    f"Unknown placeholder(s) {unknown} in "
                    f"{trans.template.email_type} ({trans.language}) "
                    f"{field_name}"
                )


class PlaceholderVocabularyTests(TestCase):
    """Sanity checks on the canonical placeholder vocabulary."""

    def test_core_placeholders_present(self):
        for key in ("client_name", "payment_reference", "service_name",
                     "salon_name", "deposit_amount", "admin_url", "hours"):
            self.assertIn(key, EMAIL_PLACEHOLDERS)

    def test_all_placeholders_match_regex(self):
        """Every placeholder key must be a valid \\w+ identifier."""
        import re
        for key in EMAIL_PLACEHOLDERS:
            self.assertTrue(
                re.match(r"^\w+$", key),
                f"Invalid placeholder key: {key!r}"
            )


class AdminFormValidationTests(TestCase):
    """EmailTemplateTranslationForm must block unknown placeholders on save."""

    def test_valid_placeholders_pass_validation(self):
        from apps.site_config.admin import EmailTemplateTranslationForm
        template = EmailTemplate.objects.get(email_type="request_received")
        trans = template.translations.get(language='hu')
        form = EmailTemplateTranslationForm(
            instance=trans,
            data={
                'template': template.pk,
                'language': 'hu',
                'subject': 'Hi {{ client_name }}',
                'body_text': 'Ref: {{ payment_reference }}',
                'body_html': '',
            },
        )
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_unknown_placeholder_in_subject_blocked(self):
        from apps.site_config.admin import EmailTemplateTranslationForm
        template = EmailTemplate.objects.get(email_type="request_received")
        trans = template.translations.get(language='hu')
        form = EmailTemplateTranslationForm(
            instance=trans,
            data={
                'template': template.pk,
                'language': 'hu',
                'subject': 'Hi {{ clietn_name }}',  # typo
                'body_text': 'Valid body',
                'body_html': '',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('clietn_name', str(form.errors['subject']))

    def test_unknown_placeholder_in_body_blocked(self):
        from apps.site_config.admin import EmailTemplateTranslationForm
        template = EmailTemplate.objects.get(email_type="expiry_reminder")
        trans = template.translations.get(language='en')
        form = EmailTemplateTranslationForm(
            instance=trans,
            data={
                'template': template.pk,
                'language': 'en',
                'subject': 'Valid',
                'body_text': 'Your {{ totally_made_up_key }} is ready',
                'body_html': '',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('body_text', form.errors)

    def test_empty_body_html_not_validated(self):
        """Empty body_html should not trigger placeholder validation."""
        from apps.site_config.admin import EmailTemplateTranslationForm
        template = EmailTemplate.objects.get(email_type="request_received")
        trans = template.translations.get(language='en')
        form = EmailTemplateTranslationForm(
            instance=trans,
            data={
                'template': template.pk,
                'language': 'en',
                'subject': 'Valid {{ client_name }}',
                'body_text': 'Valid {{ payment_reference }}',
                'body_html': '',
            },
        )
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_error_message_lists_valid_placeholders(self):
        """The validation error should mention valid placeholders for guidance."""
        from apps.site_config.admin import EmailTemplateTranslationForm
        template = EmailTemplate.objects.get(email_type="request_received")
        trans = template.translations.get(language='hu')
        form = EmailTemplateTranslationForm(
            instance=trans,
            data={
                'template': template.pk,
                'language': 'hu',
                'subject': '{{ typo_thing }}',
                'body_text': 'ok',
                'body_html': '',
            },
        )
        form.is_valid()
        error_text = str(form.errors['subject'])
        # Should mention at least some valid placeholder names
        self.assertIn('client_name', error_text)


# ──────────────────────────────────────────────────────────────
# Phase 7E — SEO Configuration Tests
# ──────────────────────────────────────────────────────────────

from apps.site_config.seo_service import resolve_seo
from apps.site_config.models import (
    GlobalSEO,
    GlobalSEOTranslation,
    PageSEO,
    PageSEOTranslation,
)


class SeedMigrationTestsSEO(TestCase):
    """Verify the 0009 SEO seed migration."""

    def test_global_seo_singleton_seeded(self):
        self.assertTrue(GlobalSEO.objects.exists())

    def test_six_static_pages_seeded(self):
        paths = set(PageSEO.objects.values_list('url_path', flat=True))
        expected = {'/', '/about/', '/contact/', '/terms/', '/privacy/', '/services/'}
        self.assertEqual(paths, expected)

    def test_all_pages_have_hu_translation(self):
        for page in PageSEO.objects.all():
            self.assertTrue(
                page.translations.filter(language='hu').exists(),
                f"Missing HU translation for {page.url_path}"
            )

    def test_all_seeded_pages_active(self):
        self.assertTrue(PageSEO.objects.filter(is_active=True).count(), 6)

    def test_global_seo_has_hu_defaults(self):
        global_seo = GlobalSEO.get_solo()
        self.assertTrue(
            global_seo.translations.filter(language='hu').exists()
        )


class PageSEOConstraintTests(TestCase):
    """CheckConstraint + clean(): exactly one of url_path/service must be set."""

    def test_url_path_only_allowed(self):
        page = PageSEO.objects.create(url_path='/test-path/', service=None)
        self.assertIsNotNone(page.pk)

    def test_service_only_allowed(self):
        from apps.services.models import Service
        svc = Service.objects.first()
        if svc is None:
            self.skipTest("No services in DB")
        page = PageSEO.objects.create(url_path=None, service=svc)
        self.assertIsNotNone(page.pk)

    def test_both_null_rejected_by_clean(self):
        """Neither url_path nor service set — clean() raises ValidationError."""
        from django.core.exceptions import ValidationError
        page = PageSEO(url_path=None, service=None)
        with self.assertRaises(ValidationError):
            page.clean()

    def test_both_set_rejected_by_clean(self):
        """Both url_path and service set — clean() raises ValidationError."""
        from django.core.exceptions import ValidationError
        from apps.services.models import Service
        svc = Service.objects.first()
        if svc is None:
            self.skipTest("No services in DB")
        page = PageSEO(url_path='/test/', service=svc)
        with self.assertRaises(ValidationError):
            page.clean()

    def test_url_path_only_passes_clean(self):
        page = PageSEO(url_path='/test/', service=None)
        page.clean()  # Should not raise

    def test_service_only_passes_clean(self):
        from apps.services.models import Service
        svc = Service.objects.first()
        if svc is None:
            self.skipTest("No services in DB")
        page = PageSEO(url_path=None, service=svc)
        page.clean()  # Should not raise


class ResolveSEOTests(TestCase):
    """SEO resolution fallback chain (spec §9.4)."""

    def test_dev_fallback_when_no_config(self):
        """When no GlobalSEO/PageSEO exists, dev fallback kicks in."""
        # Delete all SEO data
        PageSEOTranslation.objects.all().delete()
        PageSEO.objects.all().delete()
        GlobalSEOTranslation.objects.all().delete()
        GlobalSEO.objects.all().delete()

        result = resolve_seo(url_path='/', language='hu')
        self.assertIn('meta_title', result)
        self.assertIn('meta_description', result)
        # Dev fallback should have a title
        self.assertTrue(result['meta_title'])

    def test_global_defaults_used(self):
        """When no page-level override, global defaults apply."""
        result = resolve_seo(url_path='/nonexistent/', language='hu')
        global_trans = GlobalSEOTranslation.objects.get(language='hu')
        self.assertEqual(result['meta_title'], global_trans.default_meta_title)
        self.assertEqual(result['meta_description'], global_trans.default_meta_description)

    def test_page_level_overrides_global(self):
        """PageSEO should override GlobalSEO for matching url_path."""
        page = PageSEO.objects.get(url_path='/')
        page_trans = page.translations.get(language='hu')
        page_trans.meta_title = "CUSTOM HOMEPAGE TITLE"
        page_trans.save()

        result = resolve_seo(url_path='/', language='hu')
        self.assertEqual(result['meta_title'], "CUSTOM HOMEPAGE TITLE")

    def test_page_level_empty_fields_fall_through(self):
        """Empty page-level fields should fall through to global defaults."""
        page = PageSEO.objects.get(url_path='/')
        page_trans = page.translations.get(language='hu')
        original_title = page_trans.meta_title
        page_trans.meta_title = ""  # empty
        page_trans.save()

        result = resolve_seo(url_path='/', language='hu')
        # Should fall through to global default
        global_trans = GlobalSEOTranslation.objects.get(language='hu')
        self.assertEqual(result['meta_title'], global_trans.default_meta_title)

    def test_language_fallback_to_hu(self):
        """Missing language translation → HU fallback."""
        result = resolve_seo(url_path='/', language='de')
        # No DE translations seeded → should fall back to HU
        hu_trans = PageSEO.objects.get(url_path='/').translations.get(language='hu')
        self.assertEqual(result['meta_title'], hu_trans.meta_title)

    def test_canonical_url_in_result(self):
        """GlobalSEO canonical_site_url should appear in result."""
        result = resolve_seo(url_path='/', language='hu')
        self.assertTrue(result['canonical_url'])

    def test_verification_codes_in_result(self):
        """Google/Bing verification codes should be present if configured."""
        global_seo = GlobalSEO.get_solo()
        global_seo.google_verification = "test_google_code"
        global_seo.bing_verification = "test_bing_code"
        global_seo.save()

        result = resolve_seo(url_path='/', language='hu')
        self.assertEqual(result['google_verification'], "test_google_code")
        self.assertEqual(result['bing_verification'], "test_bing_code")

    def test_inactive_page_seo_ignored(self):
        """Inactive PageSEO should not override global defaults."""
        page = PageSEO.objects.get(url_path='/about/')
        page.is_active = False
        page.save()

        result = resolve_seo(url_path='/about/', language='hu')
        global_trans = GlobalSEOTranslation.objects.get(language='hu')
        self.assertEqual(result['meta_title'], global_trans.default_meta_title)


class ResolveSEOServiceTests(TestCase):
    """SEO resolution for dynamic service pages."""

    def test_service_seo_resolution(self):
        """PageSEO with service FK should resolve correctly."""
        from apps.services.models import Service
        svc = Service.objects.first()
        if svc is None:
            self.skipTest("No services in DB")

        page = PageSEO.objects.create(
            url_path=None, service=svc, is_active=True
        )
        PageSEOTranslation.objects.create(
            page_seo=page, language='hu',
            meta_title=f"Custom SEO for {svc.title}",
            meta_description="Service-specific description",
        )

        result = resolve_seo(service=svc, language='hu')
        self.assertEqual(result['meta_title'], f"Custom SEO for {svc.title}")

    def test_service_without_seo_falls_back(self):
        """Service with no PageSEO → global defaults."""
        from apps.services.models import Service
        svc = Service.objects.first()
        if svc is None:
            self.skipTest("No services in DB")

        # Ensure no PageSEO for this service
        PageSEO.objects.filter(service=svc).delete()

        result = resolve_seo(service=svc, language='hu')
        global_trans = GlobalSEOTranslation.objects.get(language='hu')
        self.assertEqual(result['meta_title'], global_trans.default_meta_title)
