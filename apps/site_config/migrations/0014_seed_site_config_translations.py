"""Seed HU translations from existing SiteConfiguration field values."""

from django.db import migrations


def seed_hu_translations(apps, schema_editor):
    SiteConfig = apps.get_model("site_config", "SiteConfiguration")
    SiteConfigTrans = apps.get_model("site_config", "SiteConfigurationTranslation")

    for config in SiteConfig.objects.all():
        # Copy existing field values into HU translation
        SiteConfigTrans.objects.update_or_create(
            site_configuration=config,
            language="hu",
            defaults={
                "business_name": config.business_name or "Afrikai Hajfonás",
                "hero_title": config.hero_title or "",
                "hero_subtitle": config.hero_subtitle or "",
            },
        )


def reverse_seed(apps, schema_editor):
    SiteConfigTrans = apps.get_model("site_config", "SiteConfigurationTranslation")
    SiteConfigTrans.objects.filter(language="hu").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_config", "0013_add_site_config_translation"),
    ]

    operations = [
        migrations.RunPython(seed_hu_translations, reverse_seed),
    ]
