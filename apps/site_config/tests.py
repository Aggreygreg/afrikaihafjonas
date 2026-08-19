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

    @classmethod
    def setUpTestData(cls):
        from apps.services.models import Service
        cls.service = Service.objects.create(
            title="Test Braids",
            description="Test description",
            base_price=50000,
            duration_minutes=240,
        )

    def test_url_path_only_allowed(self):
        page = PageSEO.objects.create(url_path='/test-path/', service=None)
        self.assertIsNotNone(page.pk)

    def test_service_only_allowed(self):
        page = PageSEO.objects.create(url_path=None, service=self.service)
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
        page = PageSEO(url_path='/test/', service=self.service)
        with self.assertRaises(ValidationError):
            page.clean()

    def test_url_path_only_passes_clean(self):
        page = PageSEO(url_path='/test/', service=None)
        page.clean()  # Should not raise

    def test_service_only_passes_clean(self):
        page = PageSEO(url_path=None, service=self.service)
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

    @classmethod
    def setUpTestData(cls):
        from apps.services.models import Service
        cls.service = Service.objects.create(
            title="Test Braids",
            description="Test description",
            base_price=50000,
            duration_minutes=240,
        )

    def test_service_seo_resolution(self):
        """PageSEO with service FK should resolve correctly."""
        svc = self.service

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
        svc = self.service

        # Ensure no PageSEO for this service
        PageSEO.objects.filter(service=svc).delete()

        result = resolve_seo(service=svc, language='hu')
        global_trans = GlobalSEOTranslation.objects.get(language='hu')
        self.assertEqual(result['meta_title'], global_trans.default_meta_title)


# ──────────────────────────────────────────────────────────────
# Public FAQ page + FAQ topics (Phase 7F)
# ──────────────────────────────────────────────────────────────
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.site_config.models import FAQTopic, FAQTopicTranslation
from apps.site_config.templatetags.content_tags import get_active_announcements


def _mk_topic(order, active=True, name_en=None):
    topic = FAQTopic.objects.create(display_order=order, is_active=active)
    FAQTopicTranslation.objects.create(
        topic=topic, language=LanguageChoices.HU, name=f"Topic-HU-{order}"
    )
    if name_en:
        FAQTopicTranslation.objects.create(
            topic=topic, language=LanguageChoices.EN, name=name_en
        )
    return topic


def _mk_faq(topic, order, question, answer="plain answer", active=True, lang=LanguageChoices.HU):
    faq = FAQ.objects.create(topic=topic, display_order=order, is_active=active)
    return FAQTranslation.objects.create(
        faq=faq, language=lang, question=question, answer=answer
    )


class FAQTopicModelTests(TestCase):
    """FAQTopic + FAQ.topic field mechanics."""

    def test_str_prefers_hu_translation(self):
        topic = FAQTopic.objects.create()
        self.assertEqual(str(topic), f"FAQ topic #{topic.pk}")
        FAQTopicTranslation.objects.create(
            topic=topic, language=LanguageChoices.HU, name="Foglalás"
        )
        self.assertEqual(str(FAQTopic.objects.get(pk=topic.pk)), "Foglalás")

    def test_unique_together_topic_language(self):
        topic = FAQTopic.objects.create()
        FAQTopicTranslation.objects.create(
            topic=topic, language=LanguageChoices.HU, name="A"
        )
        with self.assertRaises(Exception):
            FAQTopicTranslation.objects.create(
                topic=topic, language=LanguageChoices.HU, name="B"
            )

    def test_deleting_topic_keeps_faq_and_nulls_topic(self):
        topic = FAQTopic.objects.create()
        faq = FAQ.objects.create(topic=topic)
        topic.delete()
        faq.refresh_from_db()
        self.assertIsNone(faq.topic)
        self.assertTrue(FAQ.objects.filter(pk=faq.pk).exists())


class FAQPageTests(TestCase):
    """Public /faq/ page: grouping, ordering, translations, search, HTMX."""

    def setUp(self):
        # Topic 1 (order 0) created AFTER Topic 2 (order 1) — pk order must not win.
        self.topic_payments = _mk_topic(1, name_en="Payments")
        self.topic_booking = _mk_topic(0, name_en="Booking")
        _mk_faq(self.topic_booking, 1, "Cancel my request?")
        _mk_faq(self.topic_booking, 0, "How do I request an appointment?")
        _mk_faq(self.topic_payments, 0, "Which payment methods?", answer="<p>Card <strong>only</strong>.</p>")
        _mk_faq(None, 0, "Where are you located?")  # ungrouped

    def test_page_reverses_and_renders(self):
        url = reverse("faq")
        self.assertEqual(url, "/faq/")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="faq-list"')

    def test_topics_ordered_by_display_order_not_pk(self):
        response = self.client.get("/faq/")
        html = response.content.decode()
        self.assertIn("Topic-HU-0", html)
        self.assertIn("Topic-HU-1", html)
        self.assertLess(
            html.index("Topic-HU-0"), html.index("Topic-HU-1"),
            "topic display_order=0 must render before display_order=1",
        )

    def test_faq_ordering_within_topic(self):
        html = self.client.get("/faq/").content.decode()
        self.assertLess(
            html.index("How do I request an appointment?"),
            html.index("Cancel my request?"),
        )

    def test_ungrouped_faq_renders_last_under_general_section(self):
        html = self.client.get("/faq/").content.decode()
        self.assertIn("Where are you located?", html)
        # General section (topicless) comes after both named topics.
        self.assertGreater(
            html.index("Where are you located?"), html.index("Topic-HU-1"),
        )

    def test_inactive_topic_hides_its_faqs(self):
        self.topic_booking.is_active = False
        self.topic_booking.save()
        html = self.client.get("/faq/").content.decode()
        self.assertNotIn("Topic-HU-0", html)
        self.assertNotIn("How do I request an appointment?", html)
        self.assertIn("Topic-HU-1", html)  # other topic unaffected

    def test_inactive_faq_hidden(self):
        faq = FAQ.objects.get(translations__question="Cancel my request?")
        faq.is_active = False
        faq.save()
        html = self.client.get("/faq/").content.decode()
        self.assertNotIn("Cancel my request?", html)

    def test_topic_without_any_translation_hidden_with_its_faqs(self):
        orphan = FAQTopic.objects.create(display_order=5)
        FAQ.objects.create(topic=orphan, display_order=0)  # no translations anywhere
        # Degenerate topic renders no heading; FAQ without translation is skipped.
        html = self.client.get("/faq/").content.decode()
        self.assertNotIn("FAQ topic #", html)

    def test_active_language_translation_preferred(self):
        html = self.client.get("/faq/", HTTP_ACCEPT_LANGUAGE="en").content.decode()
        self.assertIn("Booking", html)
        self.assertIn("Payments", html)
        self.assertNotIn("Topic-HU-0", html)

    def test_hu_fallback_when_translation_missing(self):
        # A topic with only an HU name still renders its HU name under EN.
        hu_only = _mk_topic(2)  # no name_en → HU-only
        _mk_faq(hu_only, 0, "HU-only topic question?")
        html = self.client.get("/faq/", HTTP_ACCEPT_LANGUAGE="en").content.decode()
        self.assertIn("Topic-HU-2", html)

    def test_answer_rendered_sanitized(self):
        _mk_faq(None, 5, "Dangerous?", answer="<p>safe</p><script>alert(1)</script>")
        response = self.client.get("/faq/")
        self.assertNotContains(response, "<script>alert(1)", status_code=200)
        self.assertContains(response, "<p>safe</p>", status_code=200)

    def test_duplicate_questions_both_render(self):
        _mk_faq(None, 1, "Where are you located?")
        html = self.client.get("/faq/").content.decode()
        self.assertEqual(html.count("Where are you located?"), 2)

    # ── search ──────────────────────────────────────────────────
    def test_search_matches_question(self):
        response = self.client.get("/faq/", {"q": "appointment"})
        self.assertContains(response, "How do I request an appointment?")
        self.assertNotContains(response, "Which payment methods?", status_code=200)

    def test_search_matches_answer_text_html_stripped(self):
        response = self.client.get("/faq/", {"q": "card only"})
        self.assertContains(response, "Which payment methods?")

    def test_search_ignores_text_inside_html_tags(self):
        # 'strong' exists only as a tag name in the sanitized answer markup.
        response = self.client.get("/faq/", {"q": "strong"})
        self.assertNotContains(response, "Which payment methods?", status_code=200)

    def test_search_case_insensitive(self):
        response = self.client.get("/faq/", {"q": "APPOINTMENT"})
        self.assertContains(response, "How do I request an appointment?")

    def test_search_no_results_state(self):
        response = self.client.get("/faq/", {"q": "zebra-unicorn"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("How do I request an appointment?", response.content.decode())

    def test_search_query_escaped_not_reflected_raw(self):
        response = self.client.get("/faq/", {"q": "<script>alert(1)</script>"})
        self.assertNotContains(
            response, "<script>alert(1)</script>", status_code=200,
            msg_prefix="raw query must never be reflected unescaped: ",
        )

    def test_search_weird_but_harmless_query_values(self):
        for q in ("", "  ", "%", "_", "%%%", "ø", "?q"):
            response = self.client.get("/faq/", {"q": q})
            self.assertEqual(response.status_code, 200, msg=f"q={q!r}")

    def test_empty_query_returns_everything(self):
        response = self.client.get("/faq/", {"q": ""})
        self.assertContains(response, "How do I request an appointment?")

    # ── HTMX ────────────────────────────────────────────────────
    def test_htmx_request_returns_partial_only(self):
        response = self.client.get("/faq/", {"q": "appointment"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="faq-list"')
        self.assertNotContains(response, "<!DOCTYPE html>", status_code=200)

    def test_plain_request_returns_full_page(self):
        response = self.client.get("/faq/", {"q": "appointment"})
        self.assertContains(response, "<!DOCTYPE html>")

    def test_htmx_no_results_still_partial_with_state(self):
        response = self.client.get("/faq/", {"q": "zebra"}, HTTP_HX_REQUEST="true")
        self.assertContains(response, 'id="faq-list"')

    # ── navigation & sitemap ────────────────────────────────────
    def test_nav_links_point_at_faq_page(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="/faq/"', html)

    def test_static_sitemap_includes_faq(self):
        response = self.client.get("/sitemap-static.xml")
        self.assertContains(response, "/faq/")


class FAQPageEmptyTests(TestCase):
    """Empty-site states: nothing invented, clear placeholders."""

    def test_no_content_shows_empty_state_not_error(self):
        response = self.client.get("/faq/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="faq-list"')
        # No fabricated questions anywhere.
        self.assertNotIn("<summary", response.content.decode())

    def test_topic_without_faqs_renders_no_empty_section(self):
        _mk_topic(0)
        response = self.client.get("/faq/")
        self.assertNotIn("Topic-HU-0", response.content.decode())


# ──────────────────────────────────────────────────────────────
# Site-wide announcement banner (Phase 7F public rendering)
# ──────────────────────────────────────────────────────────────

def _mk_announcement(order=0, active=True, dismissible=True,
                     starts=None, ends=None, message="Spring offer!",
                     lang=LanguageChoices.HU, slug=None):
    slug = slug or f"banner-{order}-{LanguageChoices.values.index(lang)}"
    ann = Announcement.objects.create(
        slug=slug, is_active=active, is_dismissible=dismissible,
        display_order=order, starts_at=starts, ends_at=ends,
    )
    AnnouncementTranslation.objects.create(
        announcement=ann, language=lang, message=message,
    )
    return ann


class GetActiveAnnouncementsTagTests(TestCase):
    """Tag-level filtering: active flag, scheduling window, ordering, fallback."""

    def test_returns_active_windowless_banner(self):
        _mk_announcement()
        result = get_active_announcements()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].message, "Spring offer!")

    def test_excludes_inactive(self):
        _mk_announcement(active=False)
        self.assertEqual(get_active_announcements(), [])

    def test_excludes_future_start(self):
        _mk_announcement(starts=timezone.now() + timedelta(hours=1))
        self.assertEqual(get_active_announcements(), [])

    def test_includes_already_started(self):
        _mk_announcement(starts=timezone.now() - timedelta(seconds=1))
        self.assertEqual(len(get_active_announcements()), 1)

    def test_excludes_past_end(self):
        _mk_announcement(ends=timezone.now() - timedelta(seconds=1))
        self.assertEqual(get_active_announcements(), [])

    def test_includes_still_running(self):
        _mk_announcement(
            starts=timezone.now() - timedelta(hours=2),
            ends=timezone.now() + timedelta(hours=2),
        )
        self.assertEqual(len(get_active_announcements()), 1)

    def test_orders_by_display_order_not_pk(self):
        _mk_announcement(order=1, message="Second")
        _mk_announcement(order=0, message="First")
        result = get_active_announcements()
        self.assertEqual([t.message for t in result], ["First", "Second"])

    def test_translation_language_resolution(self):
        ann = _mk_announcement(message="HU message")
        AnnouncementTranslation.objects.create(
            announcement=ann, language=LanguageChoices.EN, message="EN message"
        )
        with override("en"):
            result = get_active_announcements()
        self.assertEqual(result[0].message, "EN message")

    def test_hu_fallback_when_active_language_missing(self):
        _mk_announcement(message="HU only")
        with override("de"):
            result = get_active_announcements()
        self.assertEqual(result[0].language, LanguageChoices.HU)

    def test_skips_announcement_without_any_translation(self):
        Announcement.objects.create(slug="mute")  # no translations at all
        self.assertEqual(get_active_announcements(), [])


class AnnouncementBannerRenderTests(TestCase):
    """Banner markup in base.html: presence, links, dismiss control."""

    def test_active_banner_renders_on_homepage(self):
        _mk_announcement(message="Nyitási akció!")
        response = self.client.get("/")
        self.assertContains(response, "Nyitási akció!", status_code=200)
        self.assertContains(response, "announcement-item", status_code=200)

    def test_no_banners_renders_no_banner_markup(self):
        response = self.client.get("/")
        self.assertNotContains(response, "announcement-item", status_code=200)

    def test_banner_link_and_text_rendered(self):
        ann = Announcement.objects.create(slug="promo")
        AnnouncementTranslation.objects.create(
            announcement=ann, language=LanguageChoices.HU, message="Akció",
            link_url="https://example.com/deal", link_text="Részletek",
        )
        response = self.client.get("/")
        self.assertContains(response, "https://example.com/deal", status_code=200)
        self.assertContains(response, "Részletek", status_code=200)

    def test_dismiss_button_only_when_dismissible(self):
        # The JS in base.html always mentions .announcement-dismiss, so the
        # assertion must target the *button markup* (data-slug), not the class name.
        _mk_announcement(dismissible=True)
        self.assertIn('data-slug="', self.client.get("/").content.decode())
        Announcement.objects.all().delete()
        _mk_announcement(dismissible=False)
        self.assertNotIn('data-slug="', self.client.get("/").content.decode())

    def test_message_is_escaped_not_injected(self):
        _mk_announcement(message="<script>alert(1)</script>")
        response = self.client.get("/")
        self.assertNotContains(response, "<script>alert(1)", status_code=200)
