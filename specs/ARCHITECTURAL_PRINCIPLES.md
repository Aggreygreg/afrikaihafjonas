# Afrikai Hajfonás — Architectural Principles: Business-Managed Content & Configuration

**Last Updated:** August 12, 2026
**Status:** Principle document — implementation tasks queued (see PROGRESS_HISTORY.md)

---

## Core Principle

Business-owned content and configuration must **not be hardcoded in application code**. Developers define the system structure, validation rules, business logic, and supported data/placeholder types; the **site administrator manages business-specific content and configuration through Django Admin**.

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

### The Litmus Test

> A routine business change—such as moving the salon, changing a phone number, replacing a bank account, adding a new payment service, changing payment instructions, updating an email, or changing SEO metadata—should **not require a developer to modify application code or redeploy the site**.

---

## 1. Business Information

**Goal:** All customer-facing business information centrally configurable via the existing `SiteConfiguration` singleton model.

**Required Fields (extending current model):**

| Field | Type | Current State |
|---|---|---|
| Salon/business name | CharField | ❌ Hardcoded in templates |
| Address | CharField | ✅ Exists |
| Address description/directions | TextField | ❌ Missing |
| Phone number | CharField | ✅ Exists |
| Email address | EmailField | ✅ Exists |
| Business/working hours | TextField or structured | ❌ Hardcoded in contact page |
| Google Maps/location link | URLField | ❌ Missing |
| Website URL | URLField | ❌ Missing |
| Logo | ImageField | ❌ Missing |
| Favicon | ImageField | ❌ Missing |
| Instagram URL | URLField | ✅ Exists |
| Facebook URL | URLField | ✅ Exists |
| TikTok URL | URLField | ✅ Exists |

**Rule:** Changes automatically reflect everywhere the data is used — templates AND email templates (via placeholder system).

---

## 2. Editable Email Templates

**Goal:** Separate email logic (when to send) from email content (subject + body). Administrator controls content via Django Admin.

**Model Design:**

```python
class EmailTemplate(models.Model):
    """Admin-managed email content with developer-defined placeholders."""
    EMAIL_TYPES = [
        ('request_received', 'Request Received'),
        ('verification_pending', 'Payment Verification Pending'),
        ('payment_verified', 'Payment Verified'),
        ('appointment_approved', 'Appointment Approved'),
        ('appointment_rejected', 'Appointment Rejected'),
        ('appointment_expired', 'Appointment Expired'),
        ('expiry_reminder', 'Expiry Reminder'),
        ('refund_notification', 'Refund Notification'),
        # Future types added here
    ]

    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    body_text = models.TextField(help_text="Plain text body. Use {{ placeholders }}.")
    body_html = models.TextField(blank=True, help_text="Optional HTML body.")
    is_active = models.BooleanField(default=True)
    language = models.CharField(max_length=5, default='hu')  # Per-language templates

    class Meta:
        unique_together = ('email_type', 'language')
```

**Developer-Controlled Placeholder Vocabulary:**

The system renders templates with a controlled context dict. Admins can use any of these in their templates:

**Client:** `{{ client_name }}`, `{{ client_email }}`, `{{ client_phone }}`, `{{ client_age }}`

**Appointment:** `{{ appointment_date }}`, `{{ appointment_time }}`, `{{ appointment_status }}`, `{{ held_until }}`

**Service:** `{{ service_name }}`, `{{ service_description }}`, `{{ service_duration }}`, `{{ service_price }}`, `{{ selected_options }}`

**Provider:** `{{ provider_name }}`

**Payment:** `{{ deposit_amount }}`, `{{ payment_method }}`, `{{ payment_reference }}`

**Business:** `{{ salon_name }}`, `{{ salon_address }}`, `{{ salon_address_description }}`, `{{ salon_phone }}`, `{{ salon_email }}`, `{{ business_hours }}`, `{{ google_maps_link }}`, `{{ website_url }}`

**Social:** `{{ instagram_url }}`, `{{ facebook_url }}`, `{{ tiktok_url }}`

**Useful Links:** `{{ guest_lookup_url }}`, `{{ privacy_policy_url }}`, `{{ terms_url }}`

**Rendering:** Developer builds a context dict → renders template via Django's string template engine → sends email. Unsupported variables render as empty strings (no crashes).

---

## 3. Administrator-Managed Payment Methods

**Goal:** Payment methods stored as database records, not hardcoded `TextChoices`.

**Model Design:**

```python
class PaymentMethod(models.Model):
    """Admin-managed payment method."""
    name = models.CharField(max_length=100)          # e.g., "Revolut", "Wise"
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)         # Instructions shown to client
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    icon = models.ImageField(upload_to='payment_icons/', blank=True)

    class Meta:
        ordering = ['display_order', 'name']
```

**Migration Strategy:**
- Seed the 4 current methods (Revolut, Wise, TransferGo, Bank Transfer) as initial records.
- `AppointmentRequest.payment_method` changes from TextChoices CharField to FK `PaymentMethod`.
- This is a **data migration** — existing AppointmentRequest records must be mapped to new PaymentMethod records.

**Admin Capabilities:** Add, edit, enable/disable, reorder, remove (if no FK references) — all without code changes.

---

## 4. Dynamic Payment Details

**Goal:** Each payment method supports admin-defined detail fields (bank name, IBAN, account holder, etc.).

**Model Design:**

```python
class PaymentDetailField(models.Model):
    """Admin-defined field for a payment method."""
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('image', 'Image Upload'),
    ]

    payment_method = models.ForeignKey(PaymentMethod, related_name='detail_fields',
                                        on_delete=models.CASCADE)
    label = models.CharField(max_length=100)          # e.g., "Account Holder"
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    value = models.TextField(blank=True)               # The actual data (text/number/etc.)
    image_value = models.ImageField(upload_to='payment_details/', blank=True)  # For image type
    display_order = models.PositiveSmallIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']
        unique_together = ('payment_method', 'label')
```

**Examples:** Bank Name, Account Holder, Account Number, IBAN, SWIFT/BIC, Routing Number, Username, Phone Number, Email Address, Payment Reference Instructions, QR Code/Image, Additional Notes.

**Rendering:** The client-facing payment step dynamically renders active fields for the selected method. No template changes needed when admin adds/removes fields.

---

## 5. Customer-Facing Content

**Goal:** Business-owned content editable from Django Admin.

**Areas:**

| Content Area | Current State | Target |
|---|---|---|
| FAQs | Hardcoded/missing | CMS model (FAQ items with question + answer, reorderable) |
| Policies & customer instructions | Hardcoded in templates | Admin-editable content blocks |
| Announcements | Missing | Banner/announcement system (dismissible) |
| Homepage marketing content | Hardcoded in templates | Editable via SiteConfiguration / content blocks |
| Static page content (About, Contact, Terms, Privacy) | Hardcoded in templates | Admin-editable rich text |
| Newsletter content | Not implemented | Future — when newsletter system introduced |

**Approach:** A generic `ContentBlock` model (key-value pairs with optional HTML) for simple cases, and dedicated models for structured content like FAQs.

---

## 6. SEO & Marketing Configuration

**Goal:** SEO metadata administrator-editable.

**Two Layers:**

**Global SEO (in SiteConfiguration or dedicated model):**

| Field | Type |
|---|---|
| Site title | CharField |
| Default meta title | CharField |
| Default meta description | TextField |
| Default keywords | TextField (comma-separated, if used) |
| Canonical site URL | URLField |
| Default OG title | CharField |
| Default OG description | TextField |
| Default OG image | ImageField |
| Search-engine verification (Google, Bing) | TextField (meta tag content) |
| Marketing/analytics identifiers | TextField (future) |

**Page-Level SEO:**

```python
class PageSEO(models.Model):
    """Per-page SEO metadata with global fallback."""
    url_path = models.CharField(max_length=200, unique=True)  # e.g., '/', '/services/', '/about/'
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    og_title = models.CharField(max_length=200, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True)
    # Blank fields fall back to global defaults
```

**Developer-Managed (Technical SEO):** sitemap.xml generation, robots.txt, canonical tag logic, structured data (JSON-LD), URL handling, multilingual hreflang implementation. These remain in code.

---

## Implementation Roadmap (Queued Tasks)

These are planned for future phases. Not started yet. See PROGRESS_HISTORY.md for current status.

### Phase 7A: Business Information Expansion
- Extend `SiteConfiguration` with all missing fields
- Update all templates to use `{{ config.* }}` instead of hardcoded values
- Update context processor if needed

### Phase 7B: Dynamic Payment Methods + Details
- Create `PaymentMethod` and `PaymentDetailField` models
- Data migration: convert `AppointmentRequest.payment_method` from TextChoices to FK
- Seed initial 4 methods with their detail fields
- Update Wizard Step 4 template to render dynamic fields
- Update Guest Lookup to display payment details

### Phase 7C: Editable Email Templates
- Create `EmailTemplate` model
- Build email rendering service (context dict → template engine → send)
- Migrate existing hardcoded emails to admin-managed templates
- Support per-language templates (HU/EN/DE)

### Phase 7D: Customer-Facing Content
- FAQ model (question, answer, order, active)
- ContentBlock model for static page content
- Update static page templates to use admin-managed content
- Announcement/banner system

### Phase 7E: SEO Configuration
- Add global SEO fields to SiteConfiguration
- Create PageSEO model for per-page metadata
- Build meta tag rendering (template tag or middleware)
- Fallback logic: page-level → global defaults

---

## Relationship to Existing Specs

This document extends (does not replace) MASTER_CONTEXT_AND_SPECS.md. Where this document specifies a new architecture for a system that already exists (e.g., payment methods), the implementation must preserve all existing business rules from the master spec:
- Deposit math remains unchanged (≥45k→20k, <45k→10k)
- 12-hour hold timer remains unchanged
- Photo upload rules remain unchanged
- Age validation remains unchanged
- Anti-patterns from Section 7 of the master spec remain in force

The core principle simply moves **where configuration lives** (from code to admin), not **what the rules are**.
