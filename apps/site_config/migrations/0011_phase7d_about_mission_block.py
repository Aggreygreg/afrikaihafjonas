# Phase 7D — add 'about_mission' ContentBlock (completes §8.4 static prose migration).
# The main 'about_page' block was already seeded in 0005; this adds the mission
# section prose that was still hardcoded in the template.

from django.db import migrations


def forwards(apps, schema_editor):
    ContentBlock = apps.get_model("site_config", "ContentBlock")
    ContentBlockTranslation = apps.get_model("site_config", "ContentBlockTranslation")

    block, _ = ContentBlock.objects.get_or_create(
        slug="about_mission",
        defaults={"display_order": 10, "is_active": True},
    )
    ContentBlockTranslation.objects.update_or_create(
        content_block=block,
        language="hu",
        defaults={
            "title": "Küldetésünk",
            "body": (
                "<p>Küldetésünk, hogy hibátlan eredményt nyújtsunk a hajad "
                "egészségének kompromisszuma nélkül. Őszinték vagyunk "
                "afelől, mit igényel minden stílus — a haj hosszától és "
                "textúrájától a megfelelő vastagságig.</p>"
                "<p>Ezért minden foglalás egy időpont-kérelem, nem pedig "
                "azonnali foglalás. Áttekintjük a fotóidat, megerősítjük, "
                "hogy hajad megfelelő a stílushoz, és csak ezután "
                "biztosítjuk a helyedet — hogy mindig elégedetten távozz "
                "székünkből.</p>"
            ),
        },
    )


def reverse(apps, schema_editor):
    ContentBlock = apps.get_model("site_config", "ContentBlock")
    ContentBlock.objects.filter(slug="about_mission").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_config", "0010_phase7e_pageseo_constraint"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
