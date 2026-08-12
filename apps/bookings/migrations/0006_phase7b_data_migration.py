"""Phase 7B: Map old payment_method TextChoices to FK + create snapshots.

Then removes the old payment_method CharField.
"""
from django.db import migrations, models


# Maps old TextChoices values to PaymentMethod slugs
SLUG_MAP = {
    'revolut': 'revolut',
    'wise': 'wise',
    'transfergo': 'transfergo',
    'bank_transfer': 'bank-transfer',  # slugify('Bank Transfer') = 'bank-transfer'
}


def migrate_payment_data(apps, schema_editor):
    AppointmentRequest = apps.get_model('bookings', 'AppointmentRequest')
    PaymentMethod = apps.get_model('bookings', 'PaymentMethod')
    AppointmentPaymentSnapshot = apps.get_model('bookings', 'AppointmentPaymentSnapshot')
    PaymentDetailField = apps.get_model('bookings', 'PaymentDetailField')

    # Build slug → PaymentMethod lookup
    method_by_slug = {pm.slug: pm for pm in PaymentMethod.objects.all()}

    for appt in AppointmentRequest.objects.all():
        old_val = getattr(appt, 'payment_method', None)

        # Map old TextChoices value to FK
        if old_val:
            slug = SLUG_MAP.get(old_val, old_val)
            pm = method_by_slug.get(slug)
            if pm:
                appt.payment_method_fk = pm

        # Set customer_language to HU for all existing records
        appt.customer_language = 'hu'

        appt.save(update_fields=['payment_method_fk', 'customer_language'])

        # Create snapshot from current detail fields (best we can do for historical records)
        if appt.payment_method_fk:
            pm = appt.payment_method_fk
            detail_snapshot = []
            for field in pm.detail_fields.filter(is_active=True).order_by('display_order'):
                detail_snapshot.append({
                    'label': field.label,
                    'field_type': field.field_type,
                    'value': field.value or (field.image_value.url if field.image_value else ''),
                })

            AppointmentPaymentSnapshot.objects.create(
                appointment=appt,
                payment_method_name=pm.name,
                payment_method_slug=pm.slug,
                detail_fields_snapshot=detail_snapshot,
            )


def reverse_migration(apps, schema_editor):
    """Reverse: remove snapshots, clear FKs."""
    AppointmentPaymentSnapshot = apps.get_model('bookings', 'AppointmentPaymentSnapshot')
    AppointmentRequest = apps.get_model('bookings', 'AppointmentRequest')

    AppointmentPaymentSnapshot.objects.all().delete()
    AppointmentRequest.objects.all().update(payment_method_fk=None)


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_phase7b_seed_payment_methods'),
    ]

    operations = [
        # Step 1: Migrate data from old field to new FK + create snapshots
        migrations.RunPython(migrate_payment_data, reverse_migration),

        # Step 2: Remove the old payment_method CharField
        migrations.RemoveField(
            model_name='appointmentrequest',
            name='payment_method',
        ),
    ]
