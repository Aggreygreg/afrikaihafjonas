# Phase 7D — seed ContentBlocks for the static pages (HU only).
# Admin can add EN/DE translations later via the admin interface.

from django.db import migrations


# Each entry: (slug, title, placeholder body). Only the base language (HU) is
# seeded — body text is intentionally a short placeholder the salon owner edits.
HU_BLOCKS = [
    (
        "about_page",
        "Rólunk",
        "<p>Ezt a tartalmat az admin felületen tudod szerkeszteni. "
        "A nyitóoldal „Rólunk” szövege ide kerül.</p>",
    ),
    (
        "terms_page",
        "Általános Szerződési Feltételek",
        "<p>Ezt a tartalmat az admin felületen tudod szerkeszteni. "
        "Az általános szerződési feltételek ide kerülnek.</p>",
    ),
    (
        "privacy_page",
        "Adatvédelmi Tájékoztató",
        "<p>Ezt a tartalmat az admin felületen tudod szerkeszteni. "
        "Az adatvédelmi tájékoztató ide kerül.</p>",
    ),
]


def create_block(apps, slug, title, body, order):
    """Create a ContentBlock + its HU translation (idempotent on slug)."""
    ContentBlock = apps.get_model("site_config", "ContentBlock")
    ContentBlockTranslation = apps.get_model("site_config", "ContentBlockTranslation")

    block, created = ContentBlock.objects.get_or_create(
        slug=slug,
        defaults={"display_order": order, "is_active": True},
    )
    ContentBlockTranslation.objects.update_or_create(
        content_block=block,
        language="hu",
        defaults={"title": title, "body": body},
    )


def forwards(apps, schema_editor):
    for index, (slug, title, body) in enumerate(HU_BLOCKS):
        create_block(apps, slug, title, body, order=index)


def reverse(apps, schema_editor):
    """Remove only the ContentBlocks this migration seeds."""
    ContentBlock = apps.get_model("site_config", "ContentBlock")
    slugs = [slug for slug, _, _ in HU_BLOCKS]
    # Cascade deletes the related ContentBlockTranslation rows automatically.
    ContentBlock.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_config", "0004_phase7d_content_models"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
