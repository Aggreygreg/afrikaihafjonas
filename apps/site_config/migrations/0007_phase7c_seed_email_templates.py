"""Seed 8 EmailTemplate parents + 24 EmailTemplateTranslations (8×3 languages).

Languages: hu (base), en, de.
The expiry_reminder templates are based on the original admin template content.
All others are new customer-facing templates with placeholder-driven content.

Idempotent: checks existence before creating.
"""
from django.db import migrations


def seed_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("site_config", "EmailTemplate")
    EmailTemplateTranslation = apps.get_model("site_config", "EmailTemplateTranslation")

    # ── Subject/body templates per type per language ──────────
    # Structure: { email_type: { language: (subject, body_text) } }

    TEMPLATES = {

        # ─── 1. request_received ─────────────────────────────
        "request_received": {
            "hu": (
                "Kérését megkaptuk — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Köszönjük, hogy az {{ salon_name }} szalonunkat választotta!\n\n"
                "Foglalási kérését megkaptuk és feldolgozás alatt áll.\n"
                "Referenciaszám: {{ payment_reference }}\n"
                "Szolgáltatás: {{ service_name }}\n"
                "Időpont: {{ appointment_date }} {{ appointment_time }}\n"
                "Stílus: {{ provider_name }}\n\n"
                "Kérjük, fizessen {{ deposit_amount }} Ft előleget a megadott fizetési módok egyikén.\n"
                "A foglalása a kifizetés igazolása után kerül megerősítésre.\n\n"
                "Foglalása állapotát itt ellenőrizheti:\n{{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "We received your request — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "Thank you for choosing {{ salon_name }}!\n\n"
                "We have received your booking request and it is being processed.\n"
                "Reference number: {{ payment_reference }}\n"
                "Service: {{ service_name }}\n"
                "Date: {{ appointment_date }} at {{ appointment_time }}\n"
                "Stylist: {{ provider_name }}\n\n"
                "Please pay the {{ deposit_amount }} HUF deposit using one of the payment methods provided.\n"
                "Your booking will be confirmed after payment verification.\n\n"
                "Check your booking status here:\n{{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Wir haben Ihre Anfrage erhalten — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Vielen Dank, dass Sie {{ salon_name }} gewählt haben!\n\n"
                "Wir haben Ihre Buchungsanfrage erhalten und sie wird bearbeitet.\n"
                "Referenznummer: {{ payment_reference }}\n"
                "Service: {{ service_name }}\n"
                "Termin: {{ appointment_date }} um {{ appointment_time }}\n"
                "Stylist: {{ provider_name }}\n\n"
                "Bitte zahlen Sie die Anzahlung von {{ deposit_amount }} HUF mit einer der angegebenen Zahlungsmethoden.\n"
                "Ihre Buchung wird nach Zahlungsverifizierung bestätigt.\n\n"
                "Buchungsstatus hier überprüfen:\n{{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
        },

        # ─── 2. verification_pending ─────────────────────────
        "verification_pending": {
            "hu": (
                "Fizetés ellenőrzése folyamatban — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Előlegfizetését megkaptuk. Jelenleg ellenőrizzük a tranzakciót.\n\n"
                "Referenciaszám: {{ payment_reference }}\n"
                "Fizetési mód: {{ payment_method_name }}\n\n"
                "Az ellenőrzés általában 1-2 órát vesz igénybe. Értesítjük, amint a fizetés megerősítést nyer.\n\n"
                "Foglalása állapota: {{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "Payment verification in progress — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "We have received your deposit payment. It is currently being verified.\n\n"
                "Reference number: {{ payment_reference }}\n"
                "Payment method: {{ payment_method_name }}\n\n"
                "Verification usually takes 1-2 hours. We will notify you once the payment is confirmed.\n\n"
                "Booking status: {{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Zahlungsüberprüfung läuft — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Wir haben Ihre Anzahlung erhalten. Sie wird derzeit überprüft.\n\n"
                "Referenznummer: {{ payment_reference }}\n"
                "Zahlungsmethode: {{ payment_method_name }}\n\n"
                "Die Überprüfung dauert in der Regel 1-2 Stunden. Wir benachrichtigen Sie, sobald die Zahlung bestätigt ist.\n\n"
                "Buchungsstatus: {{ guest_lookup_url }}\n\n"
                "{{ salon_name }}",
            ),
        },

        # ─── 3. payment_verified ──────────────────────────────
        "payment_verified": {
            "hu": (
                "Fizetés megerősítve — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Előlegfizetését sikeresen igazoltuk!\n\n"
                "Referenciaszám: {{ payment_reference }}\n"
                "Fizetett összeg: {{ deposit_amount }} Ft\n\n"
                "Foglalási kérése most adminisztrátori jóváhagyásra vár. Hamarosan értesítjük a végleges megerősítésről.\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "Payment verified — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "Your deposit payment has been successfully verified!\n\n"
                "Reference number: {{ payment_reference }}\n"
                "Amount paid: {{ deposit_amount }} HUF\n\n"
                "Your booking request is now awaiting admin approval. We will notify you of the final confirmation shortly.\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Zahlung bestätigt — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Ihre Anzahlung wurde erfolgreich verifiziert!\n\n"
                "Referenznummer: {{ payment_reference }}\n"
                "Gezahlter Betrag: {{ deposit_amount }} HUF\n\n"
                "Ihre Buchungsanfrage wartet nun auf die Administratorenfreigabe. Wir benachrichtigen Sie in Kürze über die endgültige Bestätigung.\n\n"
                "{{ salon_name }}",
            ),
        },

        # ─── 4. appointment_approved ─────────────────────────
        "appointment_approved": {
            "hu": (
                "Időpontja megerősítve! — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Örömmel értesítjük, hogy foglalási kérését MEG ERŐSÍTETTÜK!\n\n"
                "Szolgáltatás: {{ service_name }}\n"
                "Időpont: {{ appointment_date }} {{ appointment_time }}\n"
                "Stílus: {{ provider_name }}\n"
                "Referencia: {{ payment_reference }}\n\n"
                "Címünk: {{ salon_address }}\n"
                "Nyitvatartás: {{ business_hours }}\n"
                "Térkép: {{ google_maps_link }}\n\n"
                "Kérjük, pontosan érkezzen. Ha bármilyen kérdése van, hívjon minket: {{ salon_phone }}.\n\n"
                "Továbbra is itt ellenőrizheti foglalását:\n{{ guest_lookup_url }}\n\n"
                "Szeretettel várjuk!\n{{ salon_name }}",
            ),
            "en": (
                "Your appointment is confirmed! — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "We are pleased to inform you that your booking has been CONFIRMED!\n\n"
                "Service: {{ service_name }}\n"
                "Date: {{ appointment_date }} at {{ appointment_time }}\n"
                "Stylist: {{ provider_name }}\n"
                "Reference: {{ payment_reference }}\n\n"
                "Our address: {{ salon_address }}\n"
                "Hours: {{ business_hours }}\n"
                "Map: {{ google_maps_link }}\n\n"
                "Please arrive on time. If you have any questions, call us: {{ salon_phone }}.\n\n"
                "You can still check your booking here:\n{{ guest_lookup_url }}\n\n"
                "We look forward to seeing you!\n{{ salon_name }}",
            ),
            "de": (
                "Ihr Termin ist bestätigt! — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Wir freuen uns, Ihnen mitzuteilen, dass Ihre Buchung BESTÄTIGT wurde!\n\n"
                "Service: {{ service_name }}\n"
                "Termin: {{ appointment_date }} um {{ appointment_time }}\n"
                "Stylist: {{ provider_name }}\n"
                "Referenz: {{ payment_reference }}\n\n"
                "Unsere Adresse: {{ salon_address }}\n"
                "Öffnungszeiten: {{ business_hours }}\n"
                "Karte: {{ google_maps_link }}\n\n"
                "Bitte kommen Sie pünktlich. Bei Fragen rufen Sie uns an: {{ salon_phone }}.\n\n"
                "Buchungsstatus hier:\n{{ guest_lookup_url }}\n\n"
                "Wir freuen uns auf Sie!\n{{ salon_name }}",
            ),
        },

        # ─── 5. appointment_rejected ─────────────────────────
        "appointment_rejected": {
            "hu": (
                "Foglalási kérés frissítése — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Sajnáljuk, de foglalási kérését ezúttal nem tudjuk teljesíteni.\n\n"
                "Referencia: {{ payment_reference }}\n\n"
                "Ez olyan okok miatt történhetett, mint például a haj állapota nem "
                "felel meg a választott szolgáltatásnak, vagy az időpont nem megfelelő.\n\n"
                "Ha szeretné, hogy stílusaink egy másik lehetőségét megvizsgáljuk, "
                "keressen minket: {{ salon_phone }} vagy {{ salon_email }}.\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "Booking request update — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "We regret to inform you that we are unable to accommodate your booking request at this time.\n\n"
                "Reference: {{ payment_reference }}\n\n"
                "This may be due to the hair condition not matching the selected service, "
                "or the requested time slot being unavailable.\n\n"
                "If you would like us to explore other service options, please contact us: "
                "{{ salon_phone }} or {{ salon_email }}.\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Aktualisierung Ihrer Buchungsanfrage — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Wir bedauern, Ihnen mitteilen zu müssen, dass wir Ihre Buchungsanfrage "
                "zu diesem Zeitpunkt nicht erfüllen können.\n\n"
                "Referenz: {{ payment_reference }}\n\n"
                "Dies kann daran liegen, dass der Haartyp nicht zum gewählten Service passt "
                "oder der gewünschte Termin nicht verfügbar ist.\n\n"
                "Wenn Sie möchten, dass wir andere Serviceoptionen prüfen, "
                "kontaktieren Sie uns: {{ salon_phone }} oder {{ salon_email }}.\n\n"
                "{{ salon_name }}",
            ),
        },

        # ─── 6. appointment_expired ──────────────────────────
        "appointment_expired": {
            "hu": (
                "Foglalási kérés lejárt — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Foglalási kérése ({{ payment_reference }}) a visszaigazolási határidő lejárta miatt automatikusan megszűnt.\n\n"
                "Ha továbbra is szeretne időpontot foglalni, kérjük, küldje be újra kérését "
                "a weboldalunkon keresztül: {{ website_url }}\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "Booking request expired — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "Your booking request ({{ payment_reference }}) has automatically expired "
                "because the confirmation deadline has passed.\n\n"
                "If you would still like to book an appointment, please submit a new request "
                "through our website: {{ website_url }}\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Buchungsanfrage abgelaufen — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "Ihre Buchungsanfrage ({{ payment_reference }}) ist automatisch abgelaufen, "
                "da die Bestätigungsfrist verstrichen ist.\n\n"
                "Wenn Sie noch einen Termin vereinbaren möchten, senden Sie bitte eine neue Anfrage "
                "über unsere Website: {{ website_url }}\n\n"
                "{{ salon_name }}",
            ),
        },

        # ─── 7. expiry_reminder (ADMIN-FACING) ───────────────
        # This is the only email type with a LIVE trigger in the codebase
        # (send_expiry_reminders management command). It goes to the salon
        # admin, not the customer.
        "expiry_reminder": {
            "hu": (
                "[{{ salon_name }}] ⏰ {{ hours }} óra a lejáratig: {{ payment_reference }}",
                "Tisztelt Ügyvezető!\n\n"
                "Ez egy automatikus emlékeztető, hogy a lent található foglalási kérés "
                "hamarosan lejár, és intézkedésre szorul.\n\n"
                "Referencia:     {{ payment_reference }}\n"
                "Ügyfél:         {{ client_name }}\n"
                "Szolgáltatás:   {{ service_name }}\n"
                "Stílus:         {{ provider_name }}\n"
                "Időpont:        {{ appointment_date }} {{ appointment_time }}\n"
                "Státusz:        {{ appointment_status }}\n"
                "Lejárat:        {{ held_until }}\n\n"
                "Még {{ hours }} óra van hátra a foglalási határidő lejártáig. "
                "Ha nem történik intézkedés, a kérés automatikusan megszűnik.\n\n"
                "Kérés megtekintése:\n{{ admin_url }}\n\n"
                "— {{ salon_name }} Foglalási Rendszer",
            ),
            "en": (
                "[{{ salon_name }}] ⏰ {{ hours }}h until expiry: {{ payment_reference }}",
                "Hello,\n\n"
                "This is an automated reminder that the appointment request below is nearing "
                "its hold expiry and still needs admin action.\n\n"
                "Reference:     {{ payment_reference }}\n"
                "Client:        {{ client_name }}\n"
                "Service:       {{ service_name }}\n"
                "Provider:      {{ provider_name }}\n"
                "Date:          {{ appointment_date }} {{ appointment_time }}\n"
                "Status:        {{ appointment_status }}\n"
                "Hold expires:  {{ held_until }}\n\n"
                "{{ hours }} hour(s) remain before the hold window closes. "
                "If no action is taken, the request will auto-expire.\n\n"
                "Review this request now:\n{{ admin_url }}\n\n"
                "— {{ salon_name }} Booking System",
            ),
            "de": (
                "[{{ salon_name }}] ⏰ {{ hours }} Std. bis Ablauf: {{ payment_reference }}",
                "Hallo,\n\n"
                "Dies ist eine automatische Erinnerung, dass die untenstehende Buchungsanfrage "
                "kurz vor dem Ablauf steht und noch eine Administratoraktion erfordert.\n\n"
                "Referenz:      {{ payment_reference }}\n"
                "Kunde:         {{ client_name }}\n"
                "Service:       {{ service_name }}\n"
                "Stylist:       {{ provider_name }}\n"
                "Termin:        {{ appointment_date }} {{ appointment_time }}\n"
                "Status:        {{ appointment_status }}\n"
                "Ablauf:        {{ held_until }}\n\n"
                "Noch {{ hours }} Stunde(n) bis zum Ablauf. "
                "Ohne Aktion wird die Anfrage automatisch storniert.\n\n"
                "Anfrage jetzt ansehen:\n{{ admin_url }}\n\n"
                "— {{ salon_name }} Buchungssystem",
            ),
        },

        # ─── 8. refund_notification ──────────────────────────
        "refund_notification": {
            "hu": (
                "Visszatérítés feldolgozva — {{ payment_reference }}",
                "Kedves {{ client_name }}!\n\n"
                "Tájékoztatjuk, hogy az előleg visszatérítése feldolgozásra került.\n\n"
                "Referencia: {{ payment_reference }}\n"
                "Visszatérítendő összeg: {{ deposit_amount }} Ft\n"
                "Eredeti fizetési mód: {{ payment_method_name }}\n\n"
                "A visszatérítés megérkezése a fizetési szolgáltatótól függ, és akár 3-5 munkanapot is igénybe vehet.\n\n"
                "Kérdés esetén: {{ salon_phone }} vagy {{ salon_email }}\n\n"
                "{{ salon_name }}",
            ),
            "en": (
                "Refund processed — {{ payment_reference }}",
                "Dear {{ client_name }},\n\n"
                "We are writing to confirm that your deposit refund has been processed.\n\n"
                "Reference: {{ payment_reference }}\n"
                "Refund amount: {{ deposit_amount }} HUF\n"
                "Original payment method: {{ payment_method_name }}\n\n"
                "The refund may take 3-5 business days to appear, depending on your payment provider.\n\n"
                "Questions? Contact us: {{ salon_phone }} or {{ salon_email }}\n\n"
                "{{ salon_name }}",
            ),
            "de": (
                "Rückerstattung verarbeitet — {{ payment_reference }}",
                "Hallo {{ client_name }},\n\n"
                "wir bestätigen hiermit, dass Ihre Anzahlungsrückerstattung verarbeitet wurde.\n\n"
                "Referenz: {{ payment_reference }}\n"
                "Erstattungsbetrag: {{ deposit_amount }} HUF\n"
                "Ursprüngliche Zahlungsmethode: {{ payment_method_name }}\n\n"
                "Die Rückerstattung kann je nach Zahlungsanbieter 3-5 Werktage dauern.\n\n"
                "Fragen? Kontakt: {{ salon_phone }} oder {{ salon_email }}\n\n"
                "{{ salon_name }}",
            ),
        },
    }

    # ── Create parent templates ───────────────────────────────
    for email_type in TEMPLATES:
        EmailTemplate.objects.get_or_create(
            email_type=email_type,
            defaults={"is_active": True},
        )

    # ── Create translations ───────────────────────────────────
    for email_type, langs in TEMPLATES.items():
        template = EmailTemplate.objects.get(email_type=email_type)
        for lang_code, (subject, body_text) in langs.items():
            EmailTemplateTranslation.objects.get_or_create(
                template=template,
                language=lang_code,
                defaults={
                    "subject": subject,
                    "body_text": body_text,
                    "body_html": "",
                },
            )


def remove_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("site_config", "EmailTemplate")
    EmailTemplateTranslation = apps.get_model("site_config", "EmailTemplateTranslation")
    EmailTemplateTranslation.objects.all().delete()
    EmailTemplate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("site_config", "0006_phase7c_email_models"),
    ]

    operations = [
        migrations.RunPython(seed_email_templates, remove_email_templates),
    ]
