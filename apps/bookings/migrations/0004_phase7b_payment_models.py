"""Phase 7B: Create payment models + add customer_language + payment_method_fk.

Keeps the old payment_method CharField for the data migration in 0006.
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.text


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_appointmentrequest_reminder_1h_sent_and_more'),
    ]

    operations = [
        # ── New Models ──────────────────────────────────────────
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveSmallIntegerField(default=0)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='payment_icons/')),
            ],
            options={
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PaymentDetailField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('field_type', models.CharField(
                    choices=[('text', 'Text'), ('textarea', 'Text Area'), ('number', 'Number'),
                             ('email', 'Email'), ('url', 'URL'), ('image', 'Image')],
                    default='text', max_length=20,
                )),
                ('value', models.TextField(blank=True)),
                ('image_value', models.ImageField(blank=True, null=True, upload_to='payment_details/')),
                ('display_order', models.PositiveSmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('payment_method', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='detail_fields',
                    to='bookings.paymentmethod',
                )),
            ],
            options={
                'ordering': ['display_order'],
                'unique_together': {('payment_method', 'label')},
            },
        ),
        migrations.CreateModel(
            name='AppointmentPaymentSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method_name', models.CharField(max_length=100)),
                ('payment_method_slug', models.SlugField(blank=True, max_length=100)),
                ('detail_fields_snapshot', models.JSONField(default=list)),
                ('snapshot_created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_snapshot',
                    to='bookings.appointmentrequest',
                )),
            ],
        ),

        # ── Add fields to AppointmentRequest ────────────────────
        migrations.AddField(
            model_name='appointmentrequest',
            name='customer_language',
            field=models.CharField(
                choices=[('hu', 'Magyar'), ('en', 'English'), ('de', 'Deutsch')],
                default='hu',
                help_text='Captured at submission. Immutable. Drives all appointment emails.',
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name='appointmentrequest',
            name='payment_method_fk',
            field=models.ForeignKey(
                blank=True,
                help_text='FK to live PaymentMethod for admin querying. '
                          'Historical detail is in the payment_snapshot.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='appointments',
                to='bookings.paymentmethod',
            ),
        ),
    ]
