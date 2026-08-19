# Afrikai Hajfonás — Architectural Principles: Business-Managed Content & Configuration

**Last Updated:** August 19, 2026 (Revision 5 — FAQ topics + public `/faq/` page + announcement banner rendering + dead-artifact cleanup; see Decision #36)
**Status:** ✅ Implementation complete (Phase 7A–7E + 2026-08-19 content/cleanup cycle). Production-hardened, smoke-tested, 167 tests passing.

---

## Table of Contents

1. [Core Principle](#1-core-principle)
2. [Scope Boundary — Not a CMS](#2-scope-boundary--not-a-cms)
3. [Three Content Categories](#3-three-content-categories-the-foundation)
4. [Multilingual Content Strategy](#4-multilingual-content-strategy)
5. [Business Information (Phase 7A)](#5-business-information-phase-7a)
6. [Payment Methods + Historical Snapshots (Phase 7B)](#6-payment-methods--historical-snapshots-phase-7b)
7. [Editable Email Templates (Phase 7C)](#7-editable-email-templates-phase-7c)
8. [Customer-Facing Content (Phase 7D)](#8-customer-facing-content-phase-7d)
9. [SEO Configuration (Phase 7E)](#9-seo-configuration-phase-7e)
10. [Appointment Language Persistence](#10-appointment-language-persistence-cross-cutting)
11. [Email Templates vs Newsletters](#11-email-templates-vs-newsletters)
12. [Open Architectural Decisions](#12-open-architectural-decisions)

---

## 1. Core Principle

Business-owned content and configuration must **not be hardcoded in application code**. Developers define the system structure, validation rules, business logic, and supported data/placeholder types; the **site administrator manages business-specific content and configuration through Django Admin**.

> **The developer controls how the system works. The admin controls what the business currently says, displays, and accepts.**

### Separation of Responsibilities

| Developer Controls | Administrator Controls |
|---|---|
| Application structure & architecture | Business information (name, address, phone, hours) |
| Business logic (deposit math, expiry, slots) | Customer-facing content (FAQs, policies, announcements) |
| Validation rules & constraints | Email wording & templates |
| Security & access control | Payment methods (add/remove/reorder) |
| Supported data types & field types | Payment details (per-method fields) |
| Supported email placeholders | SEO metadata (titles, descriptions, OG tags) |
| Technical SEO (sitemap, robots.txt, hreflang) | Marketing & promotional content |
| Email-sending logic (when/where/trigger) | Homepage & static-page content |
| Payment snapshot logic (what gets frozen) | Payment method current configuration |

### The Litmus Test

> A routine business change — such as moving the salon, changing a phone number, replacing a bank account, adding a new payment service, changing payment instructions, updating an email, or changing SEO metadata — should **not require a developer to modify application code or redeploy the site**.

---

## 2. Scope Boundary — Not a CMS

This project is a salon appointment system, **not a general-purpose content management system**. Only make business-owned information configurable where it is genuinely useful for the salon's operation, customer communication, marketing, or maintenance.

**What this means in practice:**
- FAQs, email templates, payment methods, business info, SEO metadata → admin-managed ✅
- A drag-and-drop page builder, custom post types, arbitrary widget system → NOT building ❌
- Static page content (About, Terms, Privacy) → admin-editable text ✅
- New page creation (admin creates arbitrary new routes) → NOT building ❌

---

## 3. Three Content Categories — The Foundation

All content in the system falls into exactly one of three categories. Each has a distinct translation/management strategy. This distinction must be respected everywhere.

### Category A — Developer-Authored UI

**What:** Static interface strings written by developers in templates and Python code.

**Examples:** "Start Appointment Request", "Your request has been submitted", "Available Times", "Submit", form labels, button text.

**Translation strategy:** Django i18n / `{% trans %}` / `{% blocktrans %}` / `.po` / `.mo` files.

**Who controls:** Developer writes the English msgid and the translations in `.po` files. Administrator has no access.

**Rule:** These strings pass through `{% trans %}`. They are part of the codebase and version-controlled.

---

### Category B — Administrator-Authored Reusable Content

**What:** Business-owned content that is reused across the site or in transactional emails. Must support all three languages (HU/EN/DE).

**Examples:** FAQs, static-page content (About, Terms, Privacy body text), announcements, email template subject/body, content blocks, SEO metadata (where appropriate).

**Translation strategy:** **Language-specific records related to a shared content object.** Each content item has a parent record (for ordering, active state, shared slug) and child `Translation` records keyed by language code.

**Who controls:** Administrator creates and edits translations through Django Admin.

**Rule:** This content is **never** passed through `{% trans %}`. It is stored in the database in the language the admin typed. The system selects the correct language-specific record at render time based on the active language context.

---

### Category C — Appointment-Specific Free-Form Admin Content

**What:** One-off content created by an admin for a specific appointment or customer interaction. Not reusable.

**Examples:** `admin_notes` (visible to the client on Guest Lookup), `internal_notes` (admin-only).

**Translation strategy:** **None.** Do NOT auto-translate. Do NOT create per-language versions.

**How it works instead:**
- The appointment stores `customer_language` (see §10).
- Django Admin displays the customer's language prominently (🇭🇺 HU / 🇬🇧 EN / 🇩🇪 DE).
- The admin reads the language indicator and writes the note in the appropriate language themselves.

**Rule:** The admin knows which language the customer selected and writes accordingly. No complex multilingual system for free-form notes.

---

### Quick Reference Table

| Category | Example | Where Managed | Translation Method |
|---|---|---|---|
| **A** Developer UI | "Start Appointment Request" | `.po` files (code) | Django i18n `{% trans %}` |
| **B** Admin reusable | FAQ "How much is the deposit?" | Django Admin (DB) | Language-specific DB records |
| **C** Appointment-specific | "Please send a clearer photo of the back" | Django Admin per appointment | None — admin writes in customer's language |

---

## 4. Multilingual Content Strategy

The site supports three languages: **HU (Hungarian, base/default), EN (English), DE (German)**.

### Why not `{% trans %}` for admin content?

Django's `{% trans %}` system translates *developer-authored* strings at template-render time. It requires `.po`/`.mo` files maintained by developers. Admin-managed content is created at runtime and cannot be inserted into `.po` files. Mixing the two is architecturally incoherent.

### Chosen Design: Language-Specific Translation Records

For every admin-managed multilingual content type (FAQ, ContentBlock, EmailTemplate, SEO metadata), we use a **parent + translations** pattern:

```
ContentObject (parent)
├── ordering, active state, shared slug/key
│
├── Translation (language='hu')
│   └── title, body, etc.
├── Translation (language='en')
│   └── title, body, etc.
└── Translation (language='de')
    └── title, body, etc.
```

### Shared Language Enum

```python
class LanguageChoices(models.TextChoices):
    HUNGARIAN = 'hu', '🇭🇺 Magyar'
    ENGLISH = 'en', '🇬🇧 English'
    GERMAN = 'de', '🇩🇪 Deutsch'
```

This lives in a shared location (e.g., `apps/site_config/models.py` or a `constants` module) and is imported by all models that need language keys.

### Reusable Translation Record Pattern

Every multilingual content type follows this pattern:

```python
class Something(models.Model):
    """Parent: ordering, active state, slug. No language-specific fields."""
    # ... fields common to all languages

class SomethingTranslation(models.Model):
    """One per language. Linked to parent."""
    parent = models.ForeignKey(Something, related_name='translations',
                               on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)

    class Meta:
        unique_together = ('parent', 'language')
```

### Language Selection at Render Time

The system resolves content using this fallback chain:

1. **Active language** — the language currently active for the request (from URL prefix, session, or cookie), OR the appointment's `customer_language` for transactional emails.
2. **Base language (HU)** — if no translation exists for the active language, fall back to Hungarian.
3. **First available** — if somehow neither exists, return the first translation found (safety net).

This logic lives in a **reusable utility function** or manager method, e.g.:

```python
def get_translation(parent, language):
    """Return the best available translation for a content object."""
    return (
        parent.translations.filter(language=language).first()
        or parent.translations.filter(language='hu').first()
        or parent.translations.first()
    )
```

### Admin UX for Translations

Django Admin uses **StackedInline** for translations. The admin sees one form per language within the parent object's change page:

```python
class SomethingTranslationInline(admin.StackedInline):
    model = SomethingTranslation
    extra = 3  # Show HU, EN, DE by default
```

---

## 5. Business Information (Phase 7A)

**Goal:** All customer-facing business information centrally configurable via the existing `SiteConfiguration` singleton model.

**Multilingual?** Business info (name, address, phone, hours) is **primarily operational data**, not prose. A phone number is a phone number in every language. However, **address description/directions** and **working hours descriptions** may benefit from per-language variants.

**Decision:** `SiteConfiguration` remains a singleton with single-language fields. If address descriptions or hours descriptions need translation, use ContentBlocks (Phase 7D) keyed by slug. This keeps the singleton simple and avoids over-engineering.

**Fields (all implemented ✅ — Phase 7A):**

| Field | Type | Multilingual? | Current State |
|---|---|---|---|
| Business name | CharField | No | ✅ `business_name` |
| Address | CharField | No | ✅ `salon_address` |
| Address description/directions | TextField | Optional (via ContentBlock) | ✅ `address_description` |
| Phone number | CharField | No | ✅ `salon_phone` |
| Email address | EmailField | No | ✅ `salon_email` |
| Business/working hours | TextField | Optional (via ContentBlock) | ✅ `business_hours` |
| Google Maps/location link | URLField | No | ✅ `google_maps_link` |
| Website URL | URLField | No | ✅ `website_url` |
| Logo | ImageField | No | ✅ `logo` |
| Favicon | ImageField | No | ✅ `favicon` |
| Hero title / subtitle / image | CharField / ImageField | `{% trans %}` | ✅ `hero_title`, `hero_subtitle`, `hero_image` |
| Instagram URL | URLField | No | ✅ `instagram_url` |
| Facebook URL | URLField | No | ✅ `facebook_url` |
| TikTok URL | URLField | No | ✅ `tiktok_url` |
| Global SEO fields (title, description, OG) | Various | `GlobalSEO` + translations (Phase 7E ✅) | ✅ `GlobalSEO` model |

**Rule:** Changes automatically reflect everywhere the data is used — templates AND email templates (via placeholder system).

---

## 6. Payment Methods + Historical Snapshots (Phase 7B)

This is the most architecturally critical phase. It has **two layers** that must be kept strictly separate: the **current admin-managed configuration** and the **historical frozen snapshot** per appointment.

### 6.1 Current Payment Configuration (Admin-Managed)

The current state of what payment methods the salon accepts, with their current account details.

```python
class PaymentMethod(models.Model):
    """Admin-managed payment method. Admin can add, edit, disable, reorder.

    These are SEED DATA, not architectural constants. The four initial methods
    (Revolut, Wise, TransferGo, Bank Transfer) are seeded at migration time.
    The admin may delete them and create entirely different ones.
    """
    name = models.CharField(max_length=100)          # e.g., "Revolut", "Wise"
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    icon = models.ImageField(upload_to='payment_icons/', blank=True)

    class Meta:
        ordering = ['display_order', 'name']


class PaymentDetailField(models.Model):
    """Admin-defined field for a payment method (IBAN, account holder, QR code, etc.).

    This is the CURRENT configuration. When an appointment is created,
    these values are SNAPSHOTTED into the appointment's payment snapshot.
    Editing this record later does NOT change historical appointments.
    """
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('image', 'Image'),
    ]

    payment_method = models.ForeignKey(
        PaymentMethod, related_name='detail_fields', on_delete=models.CASCADE
    )
    label = models.CharField(max_length=100)          # e.g., "Account Holder"
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    value = models.TextField(blank=True)               # The actual current data
    image_value = models.ImageField(
        upload_to='payment_details/', blank=True      # For image type (QR codes)
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        unique_together = ('payment_method', 'label')
```

**Admin capabilities:** Add, edit, enable/disable, reorder, remove (if no FK references). All without code changes.

**Seed data, not architecture:** The current four methods are **initial seed data**. The admin may delete them and create entirely different ones.

### 6.2 Historical Payment Snapshot (Frozen at Appointment Creation)

When a customer submits an appointment request, the payment configuration that was active **at that moment** is **frozen** into the appointment record. This snapshot is permanent and immutable.

**Why this is mandatory:** An administrator may later change a payment method's IBAN, disable a method, or replace it entirely. Historical appointments must continue to represent the payment configuration that was valid when the customer submitted their request.

**Example scenario:**

| Date | Wise IBAN | What happens |
|---|---|---|
| August 2026 | `HU12 3456...` | Customer A submits appointment → snapshot records `HU12...` |
| October 2026 | `HU99 8888...` | Admin changes Wise's IBAN → `PaymentDetailField.value` updated |
| November 2026 | `HU99 8888...` | Customer B submits appointment → snapshot records `HU99...` |
| — | — | Customer A's Guest Lookup still shows `HU12...` (frozen) |

#### Snapshot Model Design

```python
class AppointmentPaymentSnapshot(models.Model):
    """Frozen copy of the payment configuration at the time of appointment submission.

    Created when the customer selects a payment method and submits (Step 4).
    NEVER updated after creation. Changes to PaymentMethod or PaymentDetailField
    do not affect existing snapshots.

    VISIBILITY:
      - payment_method_name: used by Guest Lookup (customer-visible, read-only)
      - detail_fields_snapshot: ADMIN-ONLY audit record. NEVER shown to customers.
        Per Decision #15, bank transfer details are always hidden from clients.

    Image-type detail fields are physically copied to payment_snapshots/<ref>/
    at snapshot creation time to guarantee the audit record survives later
    file deletion/replacement.
    """
    appointment = models.OneToOneField(
        'bookings.AppointmentRequest',
        related_name='payment_snapshot',
        on_delete=models.CASCADE
    )
    payment_method_name = models.CharField(max_length=100)  # e.g., "Wise"
    payment_method_slug = models.SlugField(max_length=100)   # e.g., "wise"
    # Full detail fields frozen as JSON.
    # Format: [{"label": "IBAN", "value": "HU12...", "field_type": "text"},
    #          {"label": "QR Code", "value": "/media/...", "field_type": "image"}, ...]
    detail_fields_snapshot = models.JSONField(default=list)
    snapshot_created_at = models.DateTimeField(auto_now_add=True)

    def get_detail(self, label):
        """Retrieve a frozen detail value by label."""
        for field in self.detail_fields_snapshot:
            if field['label'] == label:
                return field['value']
        return None
```

#### What Gets Frozen

When the snapshot is created, the system copies:
1. `PaymentMethod.name` → `payment_method_name`
2. `PaymentMethod.slug` → `payment_method_slug`
3. All **active** `PaymentDetailField` records for that method → `detail_fields_snapshot` (JSON array of `{label, value, field_type}`)

**Image-type fields are physically copied** to `payment_snapshots/<reference>/<label_slug>.<ext>` via Django's storage API (`default_storage.save()`). The new immutable path is stored in the JSON. This ensures that later deletion/replacement of the original image does not break the historical audit record. Text-type fields store their value directly in the JSON (no file dependency).

#### When is the Snapshot Created?

At **Step 4** (payment submission), when the customer selects a payment method and uploads proof of payment. The snapshot is created in the same transaction as the Step 4 record update.

> **Design note:** `AppointmentRequest.payment_method` (FK to live `PaymentMethod`, `on_delete=SET_NULL`) is kept for **admin querying/filtering convenience** (e.g., "show all Wise appointments"). If the admin later deletes a method, the FK becomes null but the snapshot preserves the frozen name and details.

#### Snapshot Visibility Rules (Critical — Corrects Previous Revision)

**The snapshot is an admin-only audit record.** Its `detail_fields_snapshot` (IBAN, account holder, QR codes, etc.) is **NEVER** shown to customers. This is consistent with Decision #15 and the master spec, which explicitly state: *"Bank transfer details from admin side — Always Hidden from Clients."*

Guest Lookup reads **only** `snapshot.payment_method_name` (the method name, e.g., "Wise") so that the display survives later method deletion/renaming. It does NOT read `detail_fields_snapshot`.

**Where customers see payment instructions:** On the **Step 4 wizard page** (from **live** `PaymentDetailField` records), so they can make the transfer. After submission, Guest Lookup shows only the method name + deposit + reference — never the detail fields.

#### What the Customer Sees vs What Admin Sees

| View | Source | Mutable? | Customer? |
|---|---|---|---|
| Guest Lookup — payment method **name** | `AppointmentPaymentSnapshot.payment_method_name` | ❌ Frozen | ✅ Shown |
| Guest Lookup — deposit amount | `AppointmentRequest.deposit_amount` | ❌ | ✅ Shown |
| Guest Lookup — payment reference | `AppointmentRequest.payment_reference` | ❌ | ✅ Shown |
| Guest Lookup — payment **detail fields** (IBAN, QR) | — | — | ❌ **NEVER** |
| Django Admin — appointment payment audit | `AppointmentPaymentSnapshot` (read-only inline) | ❌ Frozen | Admin only |
| Django Admin — current payment methods config | `PaymentMethod` / `PaymentDetailField` tables | ✅ Editable | Admin only |
| Wizard Step 4 — payment instructions | `PaymentMethod` (active) / `PaymentDetailField` (active) | ✅ Current config | ✅ At payment time only |

#### Migration Strategy (from TextChoices)

1. Create `PaymentMethod` and `PaymentDetailField` models.
2. **Seed migration:** create 4 methods (Revolut, Wise, TransferGo, Bank Transfer) with appropriate detail fields. These are seed data — the admin can modify or delete them later.
3. Add `payment_method_fk` FK to `AppointmentRequest` (nullable initially).
4. Add `AppointmentPaymentSnapshot` model.
5. **Data migration:** for each existing `AppointmentRequest`:
   a. Set `payment_method_fk` based on old TextChoices value → matching `PaymentMethod` slug.
   b. Create `AppointmentPaymentSnapshot` from the current `PaymentDetailField` values for that method. (Historical records get the current config snapshotted — this is the best we can do for pre-existing records.)
6. Remove old `payment_method` TextChoices CharField.

### 6.4 Step 4 Payment Instruction Display (New Phase 7B UI Requirement)

The current Step 4 page shows only payment method names (radio buttons) — no IBAN, account details, or QR codes. Customers are told to "transfer your deposit" but never shown where.

With dynamic `PaymentDetailField` records, Step 4 must:

1. Show available methods as selectable cards (from live `PaymentMethod` where `is_active=True`).
2. When a method is selected (via HTMX), display its active `PaymentDetailField` values from **live** records:
   - Text fields: label + value (e.g., "IBAN: HU12 3456...")
   - Image fields: label + `<img>` (e.g., QR code for mobile payment)
3. Customer makes the payment using the displayed instructions.
4. Customer uploads proof of payment.
5. On submit: snapshot is created from the live detail fields at that moment (with image files copied to immutable paths).

**These payment instructions are shown to the customer ONLY at Step 4 (payment time).** They are NOT shown again in Guest Lookup, confirmation page, or any other customer-facing view. Per Decision #15, bank transfer details are always hidden from clients outside the payment step.

### 6.3 Corrected Anti-Pattern Wording

The old master spec said "All payments are Manual Bank Transfers." This is inaccurate and misleading — the salon accepts Revolut, Wise, TransferGo, and Bank Transfer, and the method set is admin-configurable.

**New anti-pattern wording (master spec §7.1):**

> **No automated third-party payment gateway integrations.** Payments are manually verified using administrator-configured payment methods and instructions. The admin defines which methods are available and their account details. No Stripe, PayPal, Barion, or similar automated processing.

---

## 7. Editable Email Templates (Phase 7C)

**Goal:** Separate email logic (when to send, what triggers it) from email content (subject + body). Administrator controls content; developer controls the placeholder vocabulary and send triggers.

### 7.1 Transactional vs Marketing Emails (Strictly Separate)

**Transactional emails** are event-triggered by application logic. The developer controls the trigger; the admin controls the wording.

| Trigger Event | Email Type Key |
|---|---|
| Appointment request submitted | `request_received` |
| Payment pending verification | `verification_pending` |
| Admin verifies payment | `payment_verified` |
| Admin approves appointment | `appointment_approved` |
| Admin rejects appointment | `appointment_rejected` |
| Appointment expires (auto) | `appointment_expired` |
| Expiry reminder (2h / 1h before) | `expiry_reminder` |
| Refund issued | `refund_notification` |

**Marketing/newsletter emails** are intentionally created and sent by the admin. They are a **separate system** from transactional emails — different workflow, different model, different triggers.

> Do NOT treat newsletters as just another transactional `email_type`. If/when newsletters are built, they get their own model (`Newsletter`), their own send workflow (admin composition → preview → send to filtered audience), and their own permission scope. This is explicitly out of scope for Phase 7.

### 7.2 Email Template Model (Multilingual — Category B)

Email templates follow the **Category B multilingual pattern** (parent + translations). The parent defines the email type; each translation provides subject + body in one language.

```python
class EmailTemplate(models.Model):
    """Parent: defines the email type and active state.

    EMAIL_TYPES is a developer-controlled enum — NOT admin-extensible.
    Adding a new email type requires code changes (new trigger logic).
    """
    EMAIL_TYPES = [
        ('request_received', 'Request Received'),
        ('verification_pending', 'Payment Verification Pending'),
        ('payment_verified', 'Payment Verified'),
        ('appointment_approved', 'Appointment Approved'),
        ('appointment_rejected', 'Appointment Rejected'),
        ('appointment_expired', 'Appointment Expired'),
        ('expiry_reminder', 'Expiry Reminder'),
        ('refund_notification', 'Refund Notification'),
        # New types added by developer only — this is a code-level enum, not admin-extensible
    ]

    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES, unique=True)
    is_active = models.BooleanField(default=True)


class EmailTemplateTranslation(models.Model):
    """One per language. Subject + body text/HTML."""
    template = models.ForeignKey(
        EmailTemplate, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    subject = models.CharField(max_length=200)
    body_text = models.TextField(
        help_text="Plain text body. Use {{ placeholders }}. NO WYSIWYG — "
                  "email plain text is the primary format."
    )
    body_html = models.TextField(
        blank=True,
        help_text="Optional HTML body. Plain HTML textarea only (no WYSIWYG). "
                  "Email HTML is fragile — use simple inline styles only."
    )

    class Meta:
        unique_together = ('template', 'language')
```

**Why no WYSIWYG for email templates:** Email HTML is notoriously fragile — every email client renders differently, inline styles are required, and CSS support is fragmented. A WYSIWYG editor generates generic HTML that looks broken in Gmail/Outlook. Transactional email bodies should be primarily plain text. The optional `body_html` field is for advanced users who understand email HTML constraints — it's a plain HTML textarea, not a visual editor.

### 7.3 Language Selection for Transactional Emails

**Critical rule:** Transactional emails are sent using the **appointment's stored `customer_language`** (see §10), NOT the admin's current session language, NOT the customer's current browser language.

**Resolution:**
1. Look up `EmailTemplate` by `email_type`.
2. Look up `EmailTemplateTranslation` by `(template, appointment.customer_language)`.
3. If no translation exists for `customer_language`, fall back to HU (base).
4. Render with context dict (placeholder substitution).
5. Send.

### 7.4 Developer-Controlled Placeholder Vocabulary

The system renders templates with a controlled context dict. Admins can use any of these placeholders. Unsupported variables render as empty strings (no crashes).

**Client:** `{{ client_name }}`, `{{ client_email }}`, `{{ client_phone }}`, `{{ client_age }}`

**Appointment:** `{{ appointment_date }}`, `{{ appointment_time }}`, `{{ appointment_status }}`, `{{ held_until }}`, `{{ payment_reference }}`

**Service:** `{{ service_name }}`, `{{ service_description }}`, `{{ service_duration }}`, `{{ service_price }}`, `{{ selected_options }}`

**Provider:** `{{ provider_name }}`

**Payment:** `{{ deposit_amount }}`, `{{ payment_method_name }}`, `{{ payment_details }}` (from snapshot)

**Business:** `{{ salon_name }}`, `{{ salon_address }}`, `{{ salon_phone }}`, `{{ salon_email }}`, `{{ business_hours }}`, `{{ google_maps_link }}`, `{{ website_url }}`

**Social:** `{{ instagram_url }}`, `{{ facebook_url }}`, `{{ tiktok_url }}`

**Useful Links:** `{{ guest_lookup_url }}`, `{{ privacy_policy_url }}`, `{{ terms_url }}`

**Rendering:** Developer builds a context dict → performs **safe string substitution** (regex-based `{{ key }}` replacement, NOT Django's template engine) → sends email via Django's email backend. Unsupported variables render as empty strings (no crashes).

> **Security — Placeholder Substitution Method (Critical):**
> Do NOT use Django's `django.template.Template` engine to render admin-authored email templates. If an admin writes `{% load %}` or `{% include %}`, they could inject template tags. Instead, use simple regex-based `{{ key }}` replacement (e.g., `re.sub(r'\{\{(\w+)\}\}', lambda m: context.get(m.group(1), ''), body)`). This eliminates template tag injection entirely — admins get only `{{ placeholder }}` syntax, nothing more.

---

## 8. Customer-Facing Content (Phase 7D)

**Goal:** Business-owned reusable content editable from Django Admin, with full multilingual support.

### 8.0 Content Editing Strategy (Decided)

**Website content** (FAQ answers, ContentBlock body, Announcement message) uses a **limited WYSIWYG editor** — not Markdown, not plain text.

**Rationale:**
- The admin is a salon owner, not a developer. They will not learn Markdown syntax.
- Terms/Privacy pages need headings, bold, numbered lists — plain text can't express these.
- A limited WYSIWYG (bold/italic/headings/lists/links — no script/style/iframe) is intuitive.
- Security is handled by `bleach` sanitization with a strict tag whitelist.

**Implementation:**
- **Editor:** `django-summernote` with a deliberately limited toolbar (bold, italic, h2, h3, ul, ol, link, unlink). No image insert, no HTML source view, no format painter.
- **Sanitization:** `bleach` (or `django-bleach`) strips everything except whitelisted tags: `<p>`, `<strong>`, `<em>`, `<h2>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<a>`, `<br>`. Applied on save.
- **Rendering:** WYSIWYG output rendered inside `<div class="prose">` using `@tailwindcss/typography` plugin. Templates use `{{ block.body|safe }}` (output is pre-sanitized by bleach on save).
- **Dependencies:** `django-summernote`, `bleach` added to requirements. `@tailwindcss/typography` added to Tailwind config (build-time, not Python).

**Email templates are DIFFERENT** — see §7.2. Email `body_text` is plain textarea, `body_html` is optional plain HTML textarea. NO WYSIWYG for emails.

### 8.1 FAQ (Multilingual — Category B)

```python
class FAQTopic(models.Model):
    """Orderable, toggleable topic grouping for FAQs."""
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']


class FAQTopicTranslation(models.Model):
    """One translation per language for a topic name."""
    topic = models.ForeignKey(FAQTopic, related_name='translations', on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('topic', 'language')


class FAQ(models.Model):
    """Parent FAQ record. Optional topic grouping; orderable, toggleable."""
    topic = models.ForeignKey(
        FAQTopic, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='faqs',
        help_text="Optional grouping. FAQs without a topic appear under 'General'.",
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']


class FAQTranslation(models.Model):
    """One per language."""
    faq = models.ForeignKey(FAQ, related_name='translations', on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    question = models.CharField(max_length=300)
    answer = models.TextField()

    class Meta:
        unique_together = ('faq', 'language')
```

> **Public rendering (Aug 19, 2026):** `/faq/` (`site_config.faq_page`) groups active FAQs by active topic (display order); ungrouped FAQs fall into a final "General" section. Per-language with HU fallback. HTMX live search (question + stripped-answer substring, 400ms debounce, `#faq-list` outerHTML swap) with native GET fallback; `<details>` accordion + expand/collapse-all. See Decision #36.

### 8.2 Content Block (Multilingual — Category B)

For static page content (About, Terms, Privacy body text), announcements, and other reusable text.

```python
class ContentBlock(models.Model):
    """Parent: identified by slug, ordered, active state."""
    slug = models.SlugField(max_length=100, unique=True)  # e.g., 'about_page', 'terms_page'
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']


class ContentBlockTranslation(models.Model):
    """One per language."""
    content_block = models.ForeignKey(
        ContentBlock, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()  # WYSIWYG (django-summernote) + bleach-sanitized HTML

    class Meta:
        unique_together = ('content_block', 'language')
```

**Usage:** Templates reference `ContentBlock` by slug: `{% get_content_block 'about_page' as block %}` then render inside a prose container: `<div class="prose">{{ block.body|safe }}</div>` (output is pre-sanitized by bleach on save).

### 8.3 Announcement / Banner System (Multilingual — Category B)

```python
class Announcement(models.Model):
    """Site-wide banner. Admin controls message, active state, dismissibility."""
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['display_order']


class AnnouncementTranslation(models.Model):
    """One per language."""
    announcement = models.ForeignKey(
        Announcement, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    message = models.CharField(max_length=500)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('announcement', 'language')
```

### 8.4 Static Page Content Migration (IMPLEMENTED ✅ — Phase 7D)

The static pages (**About, Contact, Terms, Privacy** — Terms includes the deposit/refund policy as a section) have their prose served from `ContentBlock` records keyed by slug (`about_page`, `terms_page`, `privacy_page`, `about_mission`). The template structure (layout, sections, headings) remains developer-controlled; templates fall back to the original hardcoded copy if a block is inactive or missing.

**What stays in templates:** Page layout, section structure, CSS classes, non-prose elements (map embed on Contact, contact details display — the Contact page has **no form**; it renders `SiteConfiguration` contact data only).

**What lives in ContentBlocks:** Body text, policy text, about text — anything the admin should be able to edit without a developer.

---

## 9. SEO Configuration (Phase 7E)

**Goal:** SEO metadata administrator-editable, with global defaults and per-page overrides. All customer-facing SEO text is multilingual (Category B).

### 9.1 Global SEO (Dedicated Model)

```python
class GlobalSEO(models.Model):
    """Singleton: global SEO defaults used when no page-level override exists."""
    # Translatable fields handled via GlobalSEOTranslation
    canonical_site_url = models.URLField()
    og_image_default = models.ImageField(upload_to='seo/', blank=True)
    google_verification = models.CharField(max_length=200, blank=True)
    bing_verification = models.CharField(max_length=200, blank=True)
    # Singleton enforcement (same pattern as SiteConfiguration)


class GlobalSEOTranslation(models.Model):
    """Per-language global SEO text."""
    global_seo = models.ForeignKey(
        GlobalSEO, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    default_meta_title = models.CharField(max_length=200)
    default_meta_description = models.TextField()
    default_og_title = models.CharField(max_length=200, blank=True)
    default_og_description = models.TextField(blank=True)

    class Meta:
        unique_together = ('global_seo', 'language')
```

### 9.2 Page-Level SEO (Multilingual — Category B)

```python
class PageSEO(models.Model):
    """Per-page SEO metadata. Targets either a URL path (static pages)
    or a Service object (dynamic service pages).

    Exactly one of url_path / service must be set (enforced by constraint).
    """
    url_path = models.CharField(max_length=200, null=True, blank=True)
    service = models.OneToOneField(
        'services.Service', related_name='seo',
        on_delete=models.CASCADE, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(url_path__isnull=False, service__isnull=True)
                    | models.Q(url_path__isnull=True, service__isnull=False)
                ),
                name='pageseo_exactly_one_target'
            )
        ]


class PageSEOTranslation(models.Model):
    """Per-language SEO metadata for a page."""
    page_seo = models.ForeignKey(
        PageSEO, related_name='translations', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    og_title = models.CharField(max_length=200, blank=True)
    og_description = models.TextField(blank=True)

    class Meta:
        unique_together = ('page_seo', 'language')
```

### 9.3 SEO-Capable Pages

| Page | Type | SEO Managed Via | Seeded? |
|---|---|---|---|
| Homepage (`/`) | Static route | `PageSEO(url_path='/')` | ✅ |
| Services listing (`/services/`) | Static route | `PageSEO(url_path='/services/')` | ✅ |
| **Individual service (`/services/<id>/`)** | Dynamic — FK to Service | `PageSEO(service=...)` | ❌ Not seeded — created per-service in Admin when wanted |
| About (`/about/`) | Static route | `PageSEO(url_path='/about/')` | ✅ |
| Contact (`/contact/`) | Static route | `PageSEO(url_path='/contact/')` | ✅ |
| Terms (`/terms/`) | Static route | `PageSEO(url_path='/terms/')` | ✅ |
| Privacy (`/privacy/`) | Static route | `PageSEO(url_path='/privacy/')` | ✅ |
| Wizard entry (`/bookings/book/<id>/`) | Dynamic route (per service) | Inherits service detail SEO / global fallback | ❌ No dedicated PageSEO |

> **Note:** the wizard has no static `/consult/` URL — each service starts its own wizard at `/bookings/book/<service_pk>/`, so there is no single wizard landing page to give SEO metadata.

**Individual Service pages (`/services/<id>/`) are first-class SEO targets.** They are major customer-facing landing pages — customers search for specific services (e.g., "knotless box braids Budapest"). Each service gets its own SEO metadata (title, description, OG tags) per language.

### 9.4 Fallback Logic

For any page, SEO resolution follows this chain:

1. **Page-level override** — if a `PageSEOTranslation` exists for this page + active language, use it.
2. **Global default** — fall back to `GlobalSEOTranslation` for the active language.
3. **Hardcoded dev fallback** — if no admin SEO config exists at all, use a sensible default from settings (developer-controlled safety net).

### 9.5 Developer-Managed Technical SEO (NOT admin-editable)

These remain in code, maintained by developers:

- `sitemap.xml` generation (Django sitemap framework)
- `robots.txt`
- Canonical tag logic
- Structured data (JSON-LD schema for LocalBusiness, Service)
- URL/routing implementation

> **hreflang — intentionally deferred.** The site uses cookie/session-based language switching (`LocaleMiddleware`), not i18n URL patterns (`/en/`, `/de/`). Without distinct URLs per language, hreflang annotations are meaningless to search engines. Implementing hreflang would require switching to `i18n_patterns`, which is a significant architectural change. Documented as a future enhancement if URL-based i18n is adopted.

---

## 10. Appointment Language Persistence (Cross-Cutting)

This requirement affects Phase 7B, 7C, and all appointment-related views. It is documented here as a cross-cutting concern.

### Requirement

Every `AppointmentRequest` must store the customer's selected language at the time of submission as a **permanent field**. This language is used for all future communication with that customer.

```python
class AppointmentRequest(models.Model):
    # ... existing fields ...
    customer_language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.HUNGARIAN,  # HU is the base language
        help_text="Language captured at submission. Used for all appointment communication."
    )
```

### Capture Point

The language is captured when the customer submits the appointment request (Step 3 creation / Step 4 update). The value comes from the **active language at the time of form submission** — derived from Django's `get_language()` at the view level, NOT from a cookie or session that might change later.

### Immutability

Once saved, `customer_language` does **not** change. If the customer later visits the site in a different language, their appointment communication remains in the originally submitted language.

### Admin Display

Django Admin shows the customer's language prominently in the appointment detail view:

- 🇭🇺 **HU** (Magyar)
- 🇬🇧 **EN** (English)
- 🇩🇪 **DE** (Deutsch)

This informs the admin which language to use when writing `admin_notes` (Category C content).

### Email System Integration

The email rendering system (Phase 7C) reads `appointment.customer_language` to select the correct `EmailTemplateTranslation`. See §7.3.

---

## 11. Email Templates vs Newsletters

| Aspect | Transactional Email Templates | Newsletter / Marketing Emails |
|---|---|---|
| **Trigger** | Application event (appointment submitted, verified, etc.) | Admin manually creates and sends |
| **Audience** | One specific customer (the appointment owner) | Filtered group or all customers |
| **Model** | `EmailTemplate` + `EmailTemplateTranslation` (Phase 7C) | Separate `Newsletter` model (future, out of scope) |
| **Language** | Appointment's `customer_language` | Recipient's stored language or default |
| **Placeholder system** | Developer-controlled vocab, event context | Admin-authored, may use simpler tokens |

**Rule:** Do not collapse newsletters into the transactional `email_type` choices. If/when a newsletter system is needed, it gets its own architecture.

---

## 12. Architectural Decisions (ALL RESOLVED — historical record)

All questions below were decided during Phase 7 planning and are implemented. This section is retained as the decision record:

### 12.1 Rich Text Editor for Admin Content — DECIDED ✅

**Decision:** Limited WYSIWYG (`django-summernote`) for website content (FAQ, ContentBlock, Announcement). Plain textarea for email templates (`body_text`). Optional plain HTML textarea for email `body_html`. NO Markdown. See §8.0 for full rationale.

**Rationale:** The admin is a salon owner, not a developer. Markdown syntax (`**bold**`) is a learning barrier that undermines the "admin controls content independently" principle. A limited WYSIWYG toolbar with bleach sanitization is intuitive and safe. Email HTML is too fragile for WYSIWYG — emails stay plain text.

### 12.2 Global SEO Model Design — DECIDED ✅

**Decision:** Dedicated `GlobalSEO` model with translations (§9.1), NOT in `SiteConfiguration`. Keeps `SiteConfiguration` focused on business contact info. SEO is a distinct concern.

### 12.3 Payment Snapshot Timing — DECIDED ✅

**Decision:** Snapshot created at **Step 4** (payment submission), in the same transaction. See §6.2.

### 12.4 Content Block vs Dedicated Models — DECIDED ✅

**Decision:** Generic `ContentBlock` with slug keys (§8.2). Pages share the same structure (title + body), so one generic model is sufficient.

### 12.5 App Placement for New Models — DECIDED ✅ (as built)

| Model(s) | App | Rationale |
|---|---|---|
| `PaymentMethod`, `PaymentDetailField`, `AppointmentPaymentSnapshot` | `apps/bookings/` | Payment is part of the booking lifecycle |
| `SiteConfiguration` extensions | `apps/site_config/` (existing) | Already there |
| `EmailTemplate`, `EmailTemplateTranslation` | `apps/site_config/` | All admin-managed content in one app |
| `FAQ`, `ContentBlock`, `Announcement` + translations | `apps/site_config/` | Same rationale |
| `GlobalSEO`, `PageSEO` + translations | `apps/site_config/` | Same rationale |

> **Alternative considered:** A new `apps/admin_content/` app for all Category B content. Decided against — `site_config` keeps things simple. Can be refactored later if it grows.

### 12.6 `customer_language` Migration for Existing Records — DECIDED ✅

**Decision:** Default to `hu` (base language). Existing records are historical and we cannot retroactively know what language the customer was using. HU is the safest default since it's the base language and the salon is in Hungary.

### 12.7 Email Placeholder Rendering Security — DECIDED ✅

**Decision:** Use regex-based `{{ key }}` string substitution for admin-authored email templates, NOT Django's `django.template.Template` engine. See §7.4.

**Rationale:** Django's template engine would allow admins to inject `{% load %}` or `{% include %}` tags. Regex substitution limits admins to `{{ placeholder }}` only — no template tag injection possible.

### 12.8 Step 4 Payment Instruction Display — DECIDED ✅

**Decision:** Step 4 wizard page shows live `PaymentDetailField` values (IBAN, QR codes, instructions) when a payment method is selected, via HTMX. These are shown ONLY at payment time, never in Guest Lookup. See §6.4.

### 12.9 Seed Email Templates — DECIDED ✅

**Decision:** The Phase 7C data migration seeds all 8 email types x 3 languages = 24 template records with developer-authored initial content (verified in the seed audit). The admin can edit them later. Without seeded templates, the email system has nothing to send.

---

## Relationship to Existing Specs

This document extends (does not replace) `MASTER_CONTEXT_AND_SPECS.md`. Where this document specifies a new architecture for a system that already exists (e.g., payment methods), the implementation must preserve all existing business rules from the master spec:

- Deposit math remains unchanged (>=45k -> 20k, <45k -> 10k)
- 12-hour hold timer remains unchanged
- Photo upload rules remain unchanged
- Age validation remains unchanged
- Anti-patterns from Section 7 of the master spec remain in force (with corrected payment wording per §6.3)

The core principle simply moves **where configuration lives** (from code to admin), not **what the rules are**.