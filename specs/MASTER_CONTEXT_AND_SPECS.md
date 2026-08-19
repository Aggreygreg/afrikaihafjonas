# AFRIKAI HAJFONÁS – MASTER PROJECT CONTEXT & SPECIFICATION

**Last Updated:** August 17, 2026 (synced to `main` @ post-merge state)
**Role/Purpose:** This document is the absolute source of truth for all autonomous coding agents and developers working on this repository. If a feature or approach contradicts this document, this document wins.

> **See also:** `ARCHITECTURAL_PRINCIPLES.md` — comprehensive specification for Phase 7 (A-E). Covers: business-managed content principle, three content categories (developer UI / admin reusable / appointment-specific), multilingual content strategy (parent + translation records, NOT `{% trans %}` for admin content), payment method architecture with mandatory historical snapshots, appointment language persistence, transactional email system, and SEO configuration. Read before implementing any Phase 7 work.

---

## 1. Project Philosophy & Core Identity

Afrikai Hajfónás is a premium hairstyle consultation and booking platform for a salon in Hungary.

**The Pivot:** This is NOT an "instant booking" platform. Intricate braiding requires strict hair-length, age, and thickness requirements. The system is an **Appointment Request & Hold System**. Users configure a style, submit hair photos, and manually wire a deposit. The appointment is held temporarily until an administrator manually reviews and approves/rejects the request.

**Tech Stack:** Django 4.2+ (Modular apps/ architecture), PostgreSQL (prod) / SQLite (dev), HTMX (for dynamic multi-step wizards and filtering without page reloads), and Tailwind CSS.

**Currency:** Hungarian Forint (HUF) – strictly zero decimal places (e.g., 8,000 Ft).

**Multilingual (i18n):** The target market is Europe. The site must fully support Hungarian (Base/Default), English, and German. All template strings must be wrapped in `{% trans %}` tags. A language-preference popup must be presented to first-time visitors.

---

## 2. Language Preference Modal (IMPLEMENTED — Phase 6)

**What it is:** A modal that appears for first-time visitors, asking them to choose their preferred language (Hungarian, English, or German).

**Trigger:** Shown on first visit only. The modal is rendered (hidden) in `base.html` and revealed only if the visitor has no `django_language` cookie. Once a language is chosen via Django's `set_language` view, the cookie exists and the modal never appears again.

**UI (actual implementation):**
- Centered modal overlay (`#lang-modal-overlay` in `base.html`) with semi-transparent backdrop
- Three buttons: 🇬🇧 English, 🇭🇺 Magyar, 🇩🇪 Deutsch
- No "X" close button — user MUST pick a language
- A language switcher dropdown is also available in the header for later changes

**Behavior (actual implementation):**
- Each language button is its own `<form method="post" action="/i18n/setlang/">` with a CSRF token and a hidden `language` input
- Django's built-in `set_language` view activates the language, sets the `django_language` cookie (and session), and redirects back to the `next` path
- The site does **not** use URL language prefixes (`/en/`, `/de/`) — all languages share the same URL paths; `LocaleMiddleware` resolves the language from cookie/session

**Language codes:** `hu` (Hungarian), `en` (English), `de` (German)

**Translations:** complete — 341 msgids × 3 languages (HU/EN/DE), managed via the polib script workflow (`_build_po.py` → `_apply_translations.py` → `_compile_mo.py`; `.mo` files are gitignored build artifacts — run the scripts after a fresh clone).

---

## 3. Django Application Architecture & Data Models

```
apps/
├── site_config/      # Business info singleton + admin-managed content (FAQ, ContentBlock,
│                     # Announcement, EmailTemplate, SEO) + context processors
├── users/            # Custom user model (admin access)
├── providers/        # Stylists + weekly availability
├── services/         # E-Commerce engine (catalog, options, images)
├── bookings/         # Consultation engine (AppointmentRequest + wizard + payments + emails)
├── payments/         # DECOMMISSIONED (Phase 0) — empty shell, NOT in INSTALLED_APPS,
│                     # migrations intentionally deleted (see §3.1)
└── reviews/          # DELETED (intentionally scrapped — no directory exists)
```

### apps.site_config
**Purpose:** Global settings injected into all templates via a Context Processor, plus all admin-managed content models (Phase 7).

**SiteConfiguration (solo singleton — expanded in Phase 7A ✅):** business name, address, address description/directions, phone, email, business hours, Google Maps link, website URL, logo, favicon, hero title/subtitle/image, Instagram/TikTok/Facebook links.

**Content models (all with parent + per-language translation records — see ARCHITECTURAL_PRINCIPLES §3/§4):**
- `FAQ` + `FAQTranslation` + `FAQTopic` + `FAQTopicTranslation` — admin-managed FAQs and topics, surfaced publicly at `/faq/` (Aug 19, 2026): topics group FAQs by `display_order` (active only); ungrouped FAQs fall into a "General" section last; per-language with HU fallback; HTMX live search (question + stripped-answer substring, debounce 400ms) with native GET fallback; `<details>` accordion + expand/collapse-all.
- `ContentBlock` + `ContentBlockTranslation` — static page prose by slug (`about_page`, `terms_page`, `privacy_page`, `about_mission`; templates fall back to hardcoded copy when a block is inactive/missing)
- `Announcement` + `AnnouncementTranslation` — site banner system, rendered site-wide as a dismissible banner stack above the header (Aug 19, 2026): active + scheduling window (`starts_at`/`ends_at`), ordered, per-language with HU fallback, optional CTA link, dismissed client-side via localStorage keyed by slug (the `message` field is plain text, auto-escaped for safe rendering).
- `EmailTemplate` + `EmailTemplateTranslation` — 8 transactional email types × 3 languages (seeded)
- `GlobalSEO` + `GlobalSEOTranslation`, `PageSEO` + `PageSEOTranslation` — SEO metadata (Phase 7E)

**Usage:** `{{ config.salon_phone }}` available in any template; SEO metadata via the `seo` context processor.

### apps.users & apps.providers
**User:** Standard custom user model for admin access. No client accounts — clients are anonymous consultation submitters.

**Provider:** Stylist profiles.

**AvailabilityRule:** Recurring weekly shift. Fields: `provider`, `day_of_week` (0=Mon, 6=Sun), `start_time`, `end_time`.

### apps.services (The E-Commerce Engine)

**ParentCategory:** Dynamic and admin-defined (Decision #35, Aug 18, 2026 — supersedes the original "exactly three entries" rule). Any number of entries; every record renders automatically as a top-level tab on `/services/` in creation order (pk). The classic seed trio Women's → Men's → Children's preserves the original presentation; admin-created categories (e.g., "Bridal", "Locs") append at the end. Tab selection is ID-based (`?cat=<pk>`); category names are display-only and never used for query matching. Labels are single-language DB values — see Decision #35 for the translation consequence.

**ServiceCategory:** The specific braid style linked to a parent (e.g., "Knotless Box Braids").

**Service:**
- Core: `title`, `description`, `base_price`, `duration_minutes`, `is_popular`, `video_url`
- Suitability Constraints: `target_audience` (Choices: Adults 16+, Children 8-15, Everyone 8+), `best_for_hair_types`, `suitability_warning`
- Discount: `discount_percentage` (0-100, PositiveSmallIntegerField with validators)
- Formatting: `@property formatted_duration` → "2 hrs 30 mins"
- Discount Logic: `@property has_discount` → True if percentage > 0; `@property discounted_price` → Decimal math (base_price × (1 - percentage/100))

**ServiceOption:** Customizable add-ons. Fields: `group_name` (e.g., "Length"), `value` (e.g., "Waist"), `additional_price`.

**Rendering Rule:** ≤4 options in group → Radio cards (`<input type="radio" class="peer sr-only">` styled with Tailwind `peer-checked:`). >4 options in group → Standard `<select>` dropdown.

**ServiceImage:**
- M2M Matrix: `linked_options` — ManyToManyField to `ServiceOption`. One image can represent multiple combined options.
- `@property linked_options_json` → Array of option IDs for frontend JavaScript matching.
- `order` field for sort order in gallery.

### apps.bookings (The Consultation Engine)

**AppointmentRequest:** The operational hub.

| Field Group | Fields |
|------------|--------|
| Relations | `service` (FK), `provider` (FK), `selected_options` (JSONField, frozen historical snapshot) |
| Client Data | `client_name`, `client_email`, `client_phone`, `client_age` |
| Hair Data | `hair_length` (Choices: Ear, Chin, Neck, Shoulder, Armpit, Bra Strap, Mid Back, Waist, Hip), `photo_front`, `photo_side`, `photo_back` |
| Financials | `deposit_amount`, `payment_method_fk` (FK to admin-managed `PaymentMethod` model, `on_delete=SET_NULL` — implemented in Phase 7B), `payment_reference` (Auto-generated `AFH-XXXXXX`), `proof_of_payment` (**blank=True** — created at Step 3, proof added at Step 4) |
| Timers & State | `target_date`, `target_time`, `created_at`, `held_until` (default 12 hours from creation), `reminder_2h_sent`, `reminder_1h_sent` |
| Status | `pending_verification`, `pending_review`, `approved`, `rejected`, `expired` |
| Payment Status | `pending_verification`, `verified`, `rejected` |
| Language | `customer_language` (hu/en/de — captured at Step 3 submission, immutable; drives all transactional email language) |
| Notes | `admin_notes` (client-visible on Guest Lookup — Category C free-form content, NOT auto-translated), `internal_notes` (private) |

> **Payment Architecture (Phase 7B — implemented ✅):** `payment_method` migrated from hardcoded TextChoices to a dynamic `PaymentMethod` model with admin-managed `PaymentDetailField` entries (IBAN, account holder, QR codes, etc.). Each appointment has a frozen `AppointmentPaymentSnapshot` preserving the payment configuration at submission time. `payment_method_fk` uses `on_delete=SET_NULL` so historical FK references survive method deletion. See `ARCHITECTURAL_PRINCIPLES.md` §6.
>
> **Historical Snapshot (Phase 7B, mandatory):** `AppointmentPaymentSnapshot` freezes the payment configuration at submission time. Later admin edits to `PaymentMethod` or `PaymentDetailField` will NOT alter historical appointment records. See `ARCHITECTURAL_PRINCIPLES.md` §6.2.
>
> **Appointment Language (Phase 7B/7C, mandatory):** `AppointmentRequest.customer_language` (hu/en/de) is captured at Step 3 submission and used for all transactional emails. See `ARCHITECTURAL_PRINCIPLES.md` §10.

**State Machine:**
```
pending_verification → pending_review → approved
        │                    │
        └──── expired ───────┘── rejected → RefundQueue
```

**RefundQueue:** Proxy model of `AppointmentRequest` filtering to `status__in=['rejected', 'expired']`. Custom manager overrides `get_queryset`.

**Key Implementation Detail — Draft Approach:**
- Step 3 submit creates the `AppointmentRequest` with `status=pending_verification`, all client data + hair photos. `proof_of_payment` left blank (model has `blank=True`).
- Step 4 updates the existing record with payment method + proof of payment.
- Session stores `appointment_request_id` between steps.
- This avoids temp file storage for multi-step HTMX file uploads.

### apps.payments (DECOMMISSIONED)
Stripe/PayPal gateways removed in Phase 0 (commit `e2687c8`). The app directory remains as an empty, documented shell to avoid import errors; it is **commented out of `INSTALLED_APPS`** and its two migration files were **intentionally deleted**. Payment logic lives on `AppointmentRequest` + `PaymentMethod`/`PaymentDetailField`/`AppointmentPaymentSnapshot` in `apps.bookings`. Payments are manually verified using administrator-configured payment methods and instructions. No automated third-party payment gateway integrations.

> **Migration note:** the canonical applied-migration count across active apps is **47**. Any count of 49 includes the two deleted `payments` migrations from before the decommission.

### apps.reviews (DELETED)
Intentionally scrapped. No star ratings, comments, or review system.

---

## 4. Strict Business Logic & Rules

### Age Policy & Validation
- Children younger than 8 are **strictly forbidden**.
- Age validation during Step 3 of the Consultation Wizard.
- Rules: Adults (16+) → min 16; Children (8-15) → min 8; Everyone (8+) → min 8; Under 8 → always blocked.
- Client-side JS on input change (UX feedback) + server-side enforcement on submit.
- Friendly error message if age doesn't match.

### Deposit Mathematics
- Fixed flat rates based on `base_price` of the selected service.
- `base_price >= 45,000 Ft` → Deposit = 20,000 Ft
- `base_price < 45,000 Ft` → Deposit = 10,000 Ft
- Logic lives in `utils.py` (`calculate_deposit()`), never in templates.

### Time Slot Calculation
- Operates on a 30-minute interval grid.
- A slot is only rendered if `potential_start_time + service_duration_minutes <= provider_end_time`.
- A slot is blocked if it overlaps with an existing `AppointmentRequest` where `status == 'approved'` OR `held_until > timezone.now()`.

### Expiry Timers & Reminders
- Held slots default to 12 hours. If admin doesn't act, slot frees and request marks as expired.
- Background tasks (Django management command + cron, NOT Celery) must evaluate `held_until` timestamps and email the Admin:
  - Two hours before expiry
  - One hour before expiry
  - Shortly before expiry

### Seasonal Discount Engine
- Admin can bulk-apply percentage discounts to services.
- Frontend: Original price with strikethrough, new price, percentage discount badge.
- Catalog filter: "Discounted Services" filter, sorted by highest percentage discount first.

### Payment Reference Format
- Pattern: `AFH-` + 6 alphanumeric characters (e.g., `AFH-8C4D29`)
- Unique constraint on `payment_reference`
- Auto-generated in `AppointmentRequest.save()`
- Copy-to-clipboard button in Step 4

### Photo Upload Rules
- Hair photos: `.jpg`, `.jpeg`, `.png`, `.webp` — max 5MB each
- Proof of payment: `.jpg`, `.jpeg`, `.png`, `.pdf` — max 5MB
- Client-side: `accept` attribute + JS size check
- Server-side: Django form validation
- Storage paths: FLAT for now (`MEDIA_ROOT/hair_photos/` and `MEDIA_ROOT/payment_proofs/`) — no AFH reference subfolders yet. Future optimization.
- Files retained indefinitely (no auto-deletion)

---

## 5. Frontend UI/UX Mandates & User Journeys

### Journey 1: The Catalog & Discovery

**Home Page:** Dynamic Hero, Popular Services Grid (with Gender Badges: Pink for Women, Blue for Men), Language Preference Popup.

**Catalog Page:** Users switch between Parent Categories using top-level tabs generated from `ParentCategory` records (admin-defined, creation order, default = first; selection via `?cat=<pk>` — ID-based, never name-based). Clicking a tab triggers HTMX to swap the grid AND dynamically filter the sidebar dropdowns to show only relevant subcategories. Includes live keyword search and numerical `price_min`/`price_max` inputs.

### Journey 2: The E-Commerce Detail Page (SHEIN-Style)

**Layout (Left/Top):** Hero image (dynamic, switches based on selected options) + thumbnail strip.

**Layout (Right/Bottom):**
1. Service Title
2. Base Price (formatted: `8,000 Ft`) — with strikethrough if discounted
3. Discount badge (if applicable)
4. Human-Readable Duration (`@property formatted_duration`)
5. **Style Details** (description) — MUST appear ABOVE Suitability Information
6. **Suitability Information Box:**
   - Target Audience
   - Best For Hair Types
   - **IMPORTANT** warning (all caps, never "Important warning")
7. Option Selection (radio cards or dropdowns)
8. "Start Appointment Request" CTA button

**Dynamic Image Switching:**
```javascript
// Vanilla JS — listens to option changes
// Reads data attributes from radio/select inputs
// Calculates highest matching score between selected options
// and ServiceImage.linked_options_json
// Swaps hero image to best match
```

**The Option Rendering Rule (CRITICAL):**
- ≤4 options in group → `<input type="radio" class="peer sr-only">` + Tailwind `peer-checked:` styled cards. Radio dot NEVER visible.
- >4 options in group → Standard `<select>` dropdown.

### Journey 3: The Consultation Wizard (4-Step HTMX)

**Wizard Step Mapping (Our Implementation vs Master Spec):**

| Our Step | Master Spec Step | Content |
|----------|-----------------|---------|
| Step 1: Configure | *(not in spec)* | Options config (SHEIN-style radio cards, dropdowns, checkboxes) |
| Step 2: Schedule | Spec Step 1 | Provider + date + time (HTMX time slots) |
| Step 3: Details | Spec Steps 2+3 | Client info + age validation + hair data + photos + GDPR consent |
| Step 4: Review | Spec Step 4 | Deposit + AFH reference + payment method + proof + submit |

**Step 1: Service Options Configuration (Built ✅)**
- Dynamic form based on ServiceOption groups
- Radio cards for ≤4 options, dropdowns for >4, checkboxes for add-ons
- Option selection updates total price display in real-time via HTMX

**Step 2: Provider + Schedule (Built ✅)**
- Provider dropdown, Date picker, Time slot selector
- HTMX flow: Select stylist → fetch dates → select date → load time slots
- Time slots calculated by `utils.py`: 30-minute grid, duration-aware, blocked slot detection
- Session-based state management (`consult_<pk>`)

**Step 3: Client Details & Hair Data (Built ✅ — Phase 4)**
- Fields: Client Name, Email, Phone, Age
- Age validation: Client-side JS + server-side enforcement
- Hair Length: 9 visual clickable cards (Ear → Hip)
- Photo Uploads: Front, Side, Back with JS thumbnail previews (`URL.createObjectURL`)
- File validation: accept attribute + JS size check (5MB max)
- Thin hair tension warning (hardcoded text, no checkbox)
- GDPR/Privacy Policy consent checkbox (required)
- **Transition to Step 4:** Regular form POST with `enctype="multipart/form-data"`. Creates `AppointmentRequest` with `status=pending_verification`. Session stores `appointment_request_id`.

**Step 4: Finances & Submission (Built ✅ — Phase 4, dynamic methods in Phase 7B)**
- Display: Calculated deposit amount, AFH-XXXXXX reference with copy button, service/provider/date summary
- Fields: Payment method (dynamic radio cards from admin-managed `PaymentMethod` — seeded with Revolut, Wise, TransferGo, Bank Transfer; selecting one loads its live `PaymentDetailField` transfer details via HTMX), Proof of Payment (screenshot upload, accept .jpg/.jpeg/.png/.pdf, max 5MB), Policy review text, Final consent checkbox
- **Submit:** Updates existing `AppointmentRequest` with payment data, creates the frozen `AppointmentPaymentSnapshot`, sends the `verification_pending` email. Sets `held_until = now + 12 hours`. Redirects to confirmation page.

**Confirmation Page (Built ✅ — Phase 4)**
- "Your appointment request has been submitted!"
- Payment reference code (large, copyable)
- Next steps: "We'll verify your deposit and review your photos within 12 hours"
- Link to Guest Lookup: "Check your request status at /bookings/status/"
- Reference code reminder: "Save your reference: AFH-XXXXXX"

### Journey 4: Guest Lookup Page (`/bookings/status/`) (Built ✅ — Phase 4)

**Purpose:** Lightweight page where clients enter email + AFH reference code to view their appointment request status. No accounts needed.

**Form Fields:**
- Email (required)
- AFH Reference Code (required, format: `AFH-XXXXXX`)

**Lookup Logic:**
- Query `AppointmentRequest` by `client_email` + `payment_reference`
- If not found: friendly error ("No request found. Check your email and reference code.")
- If found: display status with conditional content

**Show/Hide Rules by Status:**

| Status | What to Show | What to Hide |
|--------|-------------|-------------|
| `pending_verification` | "We received your request and are verifying your deposit." + service + date/time + deposit + payment method + reference | Hair photos, admin notes |
| `pending_review` | "Your deposit is verified! We're now reviewing your hair photos." + all above + verified deposit confirmation | Hair photos |
| `approved` | "Your appointment is confirmed!" + full details (service, provider, date, time) + admin notes (if any) | — |
| `rejected` | "Unfortunately, your request was not approved." + admin notes (reason) + refund instructions + reference for tracking | Proof of payment |
| `expired` | "Your request has expired. Your hold on this time slot has ended." + "Would you like to submit a new request?" | — |

**Always Hidden from Clients:**
- Proof of payment image (bank screenshot — sensitive account/transaction info)
- Internal payment notes (admin may write "check if amount matches" etc.)
- Bank transfer details from admin side (IBAN, account holder, QR codes — these are shown ONLY at Step 4 payment time, NEVER in Guest Lookup)

> **Phase 7B note:** The `AppointmentPaymentSnapshot` preserves frozen payment details for admin audit only. Its `detail_fields_snapshot` is NEVER rendered to customers. Guest Lookup reads ONLY the frozen `payment_method_name` from the snapshot (to survive later method deletion). See `ARCHITECTURAL_PRINCIPLES.md` §6.2 and Decision #31.

**Always Shown (if present):**
- Admin notes (labeled "Admin note: ...") — transparent; admin writes professionally knowing clients see them
- Payment reference (they need it for transfer)
- Deposit amount
- Payment method
- Brief explanation of what each status means

**Implementation:**
- Regular Django view (GET shows form, POST processes lookup)
- HTMX can be used for form submission (partial page update)
- No authentication required
- Admin notes shown transparently — no internal-only toggle needed (this is hair appointments, not medical records)

### Journey 5: Admin Dashboard

**The standard Django Admin is heavily customized to serve as the daily operating system for the salon owner.**

**1. Operational Overview Dashboard:**
- Pending Reviews (Needs photo approval)
- Requests Expiring Soon (Urgent holds)
- Today's Confirmed Appointments

**2. Financial Dashboard & Refund Queue:**
- Pending Deposit Verifications (Checking bank for the transfer)
- Pending Refunds (Refund Queue)
- Completed Refunds

**The Refund Queue Architecture:** Built using a Proxy Model of `AppointmentRequest` that overrides `get_queryset` to show ONLY records where status is `rejected` or `expired`. Admins use this to see who they owe money to, manually wire it, and resolve the record.

**3. Dynamic M2M Admin Forms:**
Because ServiceOption groups are infinite (Color, Length, Cap Size, etc.), the ServiceImage admin uploader cannot have hardcoded fields.

**Implementation:** Use a custom `BaseInlineFormSet` and `ModelForm`. Inspect the parent Service, find every associated Option Group, and dynamically generate a `<select>` dropdown field in the Django Admin for every group to populate the `linked_options` M2M field.

**Reviewing a Request:**
1. Admin opens "Pending Review" request.
2. Checks hair photos against selected style options.
3. Checks proof of payment image.

**Decision Branches:**

| Action | Result |
|--------|--------|
| **Approve** | Status → `approved`. Slot becomes permanent. Customer gets confirmation email. |
| **Reject** | Status → `rejected`. Slot freed. Request moves to Refund Queue. |
| **Auto-Expire** | If no admin action within 12h → status → `expired`. Slot freed. Request moves to Refund Queue. |

---

## 6. URL Structure (actual routes — `config/urls.py` + app urls)

| URL Pattern | View | Description |
|-------------|------|-------------|
| `/` | `homepage_view` | Hero banner + Popular Services grid |
| `/about/` | `site_config.about_page` | About page (prose from `about_page` ContentBlock) |
| `/contact/` | `site_config.contact_page` | Contact info (from `SiteConfiguration`) |
| `/terms/` | `site_config.terms_page` | Terms & Conditions incl. deposit/refund policy |
| `/privacy/` | `site_config.privacy_page` | Privacy Policy |
| `/faq/` | `site_config.faq_page` | FAQ (admin-managed topics + Q&A, trilingual, HTMX search, accordion) |
| `/services/` | `services.service_list_view` | Catalog with live HTMX filtering (script included on this template — fixed Aug 18, 2026); dynamic admin-defined parent-category tabs via `?cat=<pk>` |
| `/services/<id>/` | `services.service_detail_view` | SHEIN-style product page with dynamic gallery |
| `/bookings/book/<service_pk>/` | `bookings.consult_wizard_view` | Wizard Step 1 (options config) |
| `/bookings/book/<service_pk>/step3/` | `bookings.wizard_step_3` | Wizard Step 3 (client + hair data) |
| `/bookings/book/<service_pk>/step4/` | `bookings.wizard_step_4` | Wizard Step 4 (payment + submit) |
| `/bookings/confirmation/<reference>/` | `bookings.confirmation` | Post-submit confirmation |
| `/bookings/status/` | `bookings.guest_lookup_view` | Guest Lookup (email + AFH reference) |
| `/bookings/ajax/load-slots/` | `bookings.load_available_slots_view` | HTMX time-slot loading (Step 2) |
| `/bookings/ajax/payment-detail/` | `bookings.payment_detail_fields` | HTMX payment details (Step 4) |
| `/admin/` | Django Admin | Custom operational dashboard |
| `/summernote/` | django_summernote | WYSIWYG assets |
| `/i18n/` | Django i18n URLs | `set_language` POST endpoint |
| `/robots.txt` | TemplateView | robots.txt |
| `/sitemap.xml` | sitemap index | Sectioned sitemap (`/sitemap-static.xml`, `/sitemap-services.xml`) |

---

## 7. STRICT ANTI-PATTERNS (What NOT to build)

To prevent architectural bloat and LLM hallucinations, autonomous agents are strictly forbidden from implementing the following:

1. **NO Automated Third-Party Payment Gateways:** Do not write integrations for Stripe, PayPal, Barion, etc. Payments are manually verified using administrator-configured payment methods and instructions. The admin defines which methods are available (Revolut, Wise, TransferGo, Bank Transfer initially — admin-configurable via Django Admin in Phase 7B).
2. **NO Customer Reviews:** The reviews app was intentionally scrapped. Do not create rating models or star UIs.
3. **NO Provider Logins/Dashboards:** Stylists do not log in. All reviews and approvals are handled by the Admin/Owner. Do not implement complex Role-Based Access Control (RBAC).
4. **NO Automated SMS Notifications:** Do not integrate Twilio or SMS APIs. Communication is strictly via Email.
5. **NO Multi-Location/Tenant Logic:** Do not build models mapping to different salon addresses.
6. **NO Template-based Math:** Keep Fat Models / Skinny Templates. Do not use template tags to calculate deposits or time durations.
7. **NO window.location.reload():** Do not use brute-force JS reloads to clear states unless absolutely required. Rely entirely on HTMX `hx-swap` for state transitions.
8. **NO Client Accounts:** No user registration, login, or password management. Plain text fields only.
9. **NO Decimal Currency:** HUF with zero decimal places everywhere.

---

## 8. Branching Strategy (CURRENT STATE — updated Aug 17, 2026)

- **`main`** — the stable, production branch. All Phase 1–7 work was merged here on Aug 17, 2026 (merge commit `ef16dc7`) and verified (98/98 tests, migration-integrity audit, fresh-DB migrate-from-zero). **New work branches from `main`.**
- **`main4qp`** — the *former* integration branch used during parallel agent-driven development (Phases 1–7). Fully merged into `main`; retained for history only. Do not target it with new work.
- **Feature branches** — fork from `main`, merge back into `main` when complete, then delete. (All Phase 1–7 feature branches have been deleted, locally and on origin.)
- All merged work is verified (tests + `check` + `makemigrations --check`) before merging.

### 8.1 Known Open Issues (documented, not yet fixed)

1. ~~**Catalog HTMX filtering non-functional**~~ — **FIXED Aug 18, 2026:** `service_list.html` now includes the HTMX runtime (`htmx.org@1.9.12`, per-template pattern like the wizard — the base template still does not bundle it). Verified live: gender tab click → XHR → partial swap; debounced search → swap; native no-JS form submit unaffected. Regression tests in `apps/services/tests.py`.
2. ~~**Catalog gender matching is wrong**~~ — **FIXED Aug 18, 2026 (branch `feature/dynamic-parent-categories`):** the `name__icontains` lookup ("Men's Braids" matched "Women's Braids") was eliminated by the dynamic-category change: tabs are now generated from `ParentCategory` records and selected by primary key (`?cat=<pk>`); the old `gender` name param was removed entirely. See Decision #35.
3. ~~**Gender tab highlight goes stale after an HTMX swap**~~ — **FIXED Aug 18, 2026 (same branch):** `switchCategory()` now syncs the active pill classes client-side (tabs sit outside the swapped `#services-wrapper`, so server-rendered classes cannot update on swap). Verified live in the browser.
4. ~~**No public FAQ page**~~ — **FIXED Aug 19, 2026:** the `FAQ`/`FAQTranslation` models now also have `FAQTopic`/`FAQTopicTranslation`, and a public `/faq/` view + templates render them (topics group FAQs, trilingual with HU fallback, HTMX search, accordion). Nav links resolve to the real page; sitemap includes it. See Decision #36.
5. ~~**`SECURE_REDIRECT_EXEMPT` lists `/health-check/`**~~ — **FIXED Aug 19, 2026:** the dead config line was removed (no consumer; gunicorn/nginx serve directly). See Decision #36.
6. ~~**`Dockerfile` is a minimal stub**~~ — **FIXED Aug 19, 2026:** the scaffold-era `Dockerfile` and `docker-compose.yml` were removed entirely (never functional; the venv flow is the only supported setup). See Decision #36.
7. ~~**Legacy `media/` directory**~~ — **FIXED Aug 19, 2026:** the legacy empty `media/` dir was removed, and the 4 dev `ServiceImage` rows were repointed to real tracked files in `mediafiles/`. This is dev/demo data — in production the administrator manages service images; no permanent production ownership of the current demo images is claimed. See Decision #36.

---

## 9. Data Flow Diagram

```
Client                    Server                      Admin
  │                         │                           │
  ├─ Browse catalog ────────┤                           │
  ├─ Select service/options ┤                           │
  ├─ Start Consultation ────┤                           │
  │   ├─ Step 1: Options    │                           │
  │   ├─ Step 2: Scheduling │── HTMX partials ──►       │
  │   ├─ Step 3: Client+Hair│── Create AppointmentReq ──┤
  │   └─ Step 4: Finances   │── Update with payment ────┤
  │                         │   (slot held 12h)         │
  │                         │                           ├─ Review photos
  │                         │                           ├─ Verify payment
  │                         │   ◄── Approve/Reject ─────┤
  │◄── Confirmation page ───┤                           │
  │                         │                           │
  ├─ Guest Lookup ──────────┤                           │
  │  (email + AFH ref)      │── Return status ─────────►│
```
