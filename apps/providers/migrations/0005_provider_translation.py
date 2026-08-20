# Generated for Decision #40 — convert Provider.bio from per-language
# columns (bio/bio_en/bio_de) to the standard parent+Translation pattern
# (ProviderTranslation), matching all other Category B multilingual models.

from django.db import migrations, models


def copy_bios_to_translations(apps, schema_editor):
    """Copy existing bio/bio_en/bio_de values into ProviderTranslation rows."""
    Provider = apps.get_model("providers", "Provider")
    ProviderTranslation = apps.get_model("providers", "ProviderTranslation")

    for provider in Provider.objects.all():
        # HU (base) — always create if bio is non-empty
        if provider.bio:
            ProviderTranslation.objects.get_or_create(
                provider=provider,
                language="hu",
                defaults={"bio": provider.bio},
            )
        # EN
        if provider.bio_en:
            ProviderTranslation.objects.get_or_create(
                provider=provider,
                language="en",
                defaults={"bio": provider.bio_en},
            )
        # DE
        if provider.bio_de:
            ProviderTranslation.objects.get_or_create(
                provider=provider,
                language="de",
                defaults={"bio": provider.bio_de},
            )


def reverse_migration(apps, schema_editor):
    """Reverse: no-op (data would need to be reconstructed from translations)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("providers", "0004_add_provider_multilingual_bio"),
    ]

    operations = [
        # 1. Create ProviderTranslation model
        migrations.CreateModel(
            name="ProviderTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[("hu", "Magyar"), ("en", "English"), ("de", "Deutsch")],
                        max_length=2,
                    ),
                ),
                (
                    "bio",
                    models.TextField(
                        blank=True, help_text="Stylist bio in this language."
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="translations",
                        to="providers.provider",
                    ),
                ),
            ],
            options={
                "verbose_name": "Provider translation",
                "verbose_name_plural": "Provider translations",
                "unique_together": {("provider", "language")},
            },
        ),
        # 2. Copy existing bio data into translations
        migrations.RunPython(copy_bios_to_translations, reverse_migration),
        # 3. Remove per-language bio columns from Provider
        migrations.RemoveField(
            model_name="provider",
            name="bio",
        ),
        migrations.RemoveField(
            model_name="provider",
            name="bio_en",
        ),
        migrations.RemoveField(
            model_name="provider",
            name="bio_de",
        ),
    ]
