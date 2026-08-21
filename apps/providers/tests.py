from django.db import IntegrityError
from django.test import TestCase
from django.utils import translation

from apps.providers.models import Provider, ProviderTranslation


class ProviderTranslationTests(TestCase):
    """Regression tests for Decision #40 — Provider.bio lives in
    ProviderTranslation (parent + language rows), with the standard
    fallback chain: active language → HU → first available.

    Also guards Decision #41's verification: the old column scheme was
    bio (HU base, no suffix) + bio_en + bio_de; the 0005 data migration
    copies each non-empty column to its language row. These tests pin
    the runtime behavior that migration result relies on.
    """

    def setUp(self):
        self.provider = Provider.objects.create(display_name="Test Stylist")

    def _add(self, lang, bio):
        return ProviderTranslation.objects.create(
            provider=self.provider, language=lang, bio=bio
        )

    def test_hu_only_serves_hu_in_every_language(self):
        """Provider with only a HU row (e.g. post-migration default) —
        EN/DE visitors get the HU bio via fallback, never an error."""
        self._add("hu", "Magyar bio")
        for lang in ("hu", "en", "de"):
            with translation.override(lang):
                self.assertEqual(self.provider.display_bio, "Magyar bio")

    def test_all_languages_each_served(self):
        """HU/EN/DE all present → each active language gets its own bio."""
        self._add("hu", "Magyar bio")
        self._add("en", "English bio")
        self._add("de", "Deutsche Bio")
        cases = (("hu", "Magyar bio"), ("en", "English bio"), ("de", "Deutsche Bio"))
        for lang, expected in cases:
            with translation.override(lang):
                self.assertEqual(self.provider.display_bio, expected)

    def test_missing_language_falls_back_to_hu_not_first(self):
        """No EN row → EN visitors get HU (base), even when a DE row exists."""
        self._add("hu", "Magyar bio")
        self._add("de", "Deutsche Bio")
        with translation.override("en"):
            self.assertEqual(self.provider.display_bio, "Magyar bio")

    def test_no_translations_empty_string(self):
        """Provider with zero translation rows → display_bio is ''."""
        self.assertEqual(self.provider.display_bio, "")

    def test_explicit_language_argument(self):
        """get_translation(lang) returns that language's row directly."""
        self._add("hu", "Magyar bio")
        self._add("de", "Deutsche Bio")
        self.assertEqual(self.provider.get_translation("de").bio, "Deutsche Bio")
        self.assertEqual(self.provider.get_translation("hu").bio, "Magyar bio")

    def test_provider_language_unique_together(self):
        """Duplicate (provider, language) pair is rejected at the DB level."""
        self._add("hu", "Magyar bio")
        with self.assertRaises(IntegrityError):
            ProviderTranslation.objects.create(
                provider=self.provider, language="hu", bio="Második magyar bio"
            )
