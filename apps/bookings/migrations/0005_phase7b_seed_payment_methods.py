"""Phase 7B: Seed 4 initial payment methods with detail fields."""
from django.db import migrations
from django.utils.text import slugify


def seed_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('bookings', 'PaymentMethod')
    PaymentDetailField = apps.get_model('bookings', 'PaymentDetailField')

    methods = [
        {
            'name': 'Revolut',
            'display_order': 0,
            'details': [
                {'label': 'Account Holder', 'field_type': 'text', 'value': ''},
                {'label': 'IBAN / Account', 'field_type': 'text', 'value': ''},
            ],
        },
        {
            'name': 'Wise',
            'display_order': 1,
            'details': [
                {'label': 'Account Holder', 'field_type': 'text', 'value': ''},
                {'label': 'IBAN / Account', 'field_type': 'text', 'value': ''},
            ],
        },
        {
            'name': 'TransferGo',
            'display_order': 2,
            'details': [
                {'label': 'Account Holder', 'field_type': 'text', 'value': ''},
                {'label': 'IBAN / Account', 'field_type': 'text', 'value': ''},
            ],
        },
        {
            'name': 'Bank Transfer',
            'display_order': 3,
            'details': [
                {'label': 'Account Holder', 'field_type': 'text', 'value': ''},
                {'label': 'IBAN', 'field_type': 'text', 'value': ''},
                {'label': 'Bank Name', 'field_type': 'text', 'value': ''},
            ],
        },
    ]

    for method_data in methods:
        pm = PaymentMethod.objects.create(
            name=method_data['name'],
            slug=slugify(method_data['name']),
            is_active=True,
            display_order=method_data['display_order'],
        )
        for i, detail in enumerate(method_data['details']):
            PaymentDetailField.objects.create(
                payment_method=pm,
                label=detail['label'],
                field_type=detail['field_type'],
                value=detail['value'],
                display_order=i,
                is_active=True,
            )


def remove_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('bookings', 'PaymentMethod')
    PaymentDetailField = apps.get_model('bookings', 'PaymentDetailField')
    PaymentDetailField.objects.all().delete()
    PaymentMethod.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_phase7b_payment_models'),
    ]

    operations = [
        migrations.RunPython(seed_payment_methods, remove_payment_methods),
    ]
