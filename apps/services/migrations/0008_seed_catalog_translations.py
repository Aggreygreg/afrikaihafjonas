"""Data migration: copy existing single-language field values to HU translations.

Decision #38: Full customer-facing multilingual support. This migration
creates the base-language (HU) translations for every catalog entity from
the existing single-language fields, so no data is lost when those fields
are removed in the next migration.
"""
from django.db import migrations


def copy_catalog_to_hu_translations(apps, schema_editor):
    ParentCategory = apps.get_model('services', 'ParentCategory')
    ParentCategoryTranslation = apps.get_model('services', 'ParentCategoryTranslation')
    ServiceCategory = apps.get_model('services', 'ServiceCategory')
    ServiceCategoryTranslation = apps.get_model('services', 'ServiceCategoryTranslation')
    Service = apps.get_model('services', 'Service')
    ServiceTranslation = apps.get_model('services', 'ServiceTranslation')
    ServiceOption = apps.get_model('services', 'ServiceOption')
    ServiceOptionTranslation = apps.get_model('services', 'ServiceOptionTranslation')

    HU = 'hu'

    for pc in ParentCategory.objects.all():
        ParentCategoryTranslation.objects.get_or_create(
            parent_category=pc, language=HU,
            defaults={'name': pc.name or f'Category {pc.pk}'},
        )

    for sc in ServiceCategory.objects.all():
        ServiceCategoryTranslation.objects.get_or_create(
            service_category=sc, language=HU,
            defaults={'name': sc.name or f'Subcategory {sc.pk}'},
        )

    for svc in Service.objects.all():
        ServiceTranslation.objects.get_or_create(
            service=svc, language=HU,
            defaults={
                'title': svc.title or f'Service {svc.pk}',
                'description': svc.description or '',
                'best_for_hair_types': svc.best_for_hair_types or '',
                'suitability_warning': svc.suitability_warning or '',
            },
        )

    for opt in ServiceOption.objects.all():
        ServiceOptionTranslation.objects.get_or_create(
            service_option=opt, language=HU,
            defaults={
                'group_name': opt.group_name or '',
                'value': opt.value or '',
            },
        )


def reverse_translations(apps, schema_editor):
    """No-op reverse: translations are additive and safe to leave."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0007_add_translation_models'),
    ]

    operations = [
        migrations.RunPython(copy_catalog_to_hu_translations, reverse_translations),
    ]
