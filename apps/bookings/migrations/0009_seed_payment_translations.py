"""Data migration: copy existing payment field values to HU translations.

Decision #38: Full customer-facing multilingual support. This migration
creates the base-language (HU) translations for PaymentMethod.name and
PaymentDetailField.label from the existing single-language fields.
"""
from django.db import migrations


def copy_payment_to_hu_translations(apps, schema_editor):
    PaymentMethod = apps.get_model('bookings', 'PaymentMethod')
    PaymentMethodTranslation = apps.get_model('bookings', 'PaymentMethodTranslation')
    PaymentDetailField = apps.get_model('bookings', 'PaymentDetailField')
    PaymentDetailFieldTranslation = apps.get_model('bookings', 'PaymentDetailFieldTranslation')

    HU = 'hu'

    for pm in PaymentMethod.objects.all():
        PaymentMethodTranslation.objects.get_or_create(
            payment_method=pm, language=HU,
            defaults={'name': pm.name or f'Payment method {pm.pk}'},
        )

    for pdf in PaymentDetailField.objects.all():
        PaymentDetailFieldTranslation.objects.get_or_create(
            payment_detail_field=pdf, language=HU,
            defaults={'label': pdf.label or f'Field {pdf.pk}'},
        )


def reverse_translations(apps, schema_editor):
    """No-op reverse: translations are additive and safe to leave."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0008_add_translation_models'),
    ]

    operations = [
        migrations.RunPython(copy_payment_to_hu_translations, reverse_translations),
    ]
