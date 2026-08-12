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
