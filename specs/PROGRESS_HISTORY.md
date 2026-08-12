# Afrikai Hajfonás — Progress History

**Last Updated:** August 12, 2026

---

## Project Timeline

### Phase 0: Cleanup ✅ (Aug 10, 2026)
- Decommissioned `apps.payments` (Stripe/PayPal removed)
- Fixed `Payment` model `on_delete=PROTECT` migration dependency
- Cleaned branch structure
- Configured SQLite for local dev, console email backend

### Phase 1: Data Layer ✅ (Aug 10, 2026)
- Built `AppointmentRequest` model with all spec fields
- Built `RefundQueue` proxy model with custom manager
- Created all migrations
- State machine: `pending_verification` → `pending_review` → `approved` / `rejected` / `expired`
- `ServiceImage.linked_options` M2M + `linked_options_json` property
- `Service.discount_percentage`, `has_discount`, `discounted_price`, `formatted_duration`
- `calculate_deposit()` utility (≥45k→20k, <45k→10k)
- `get_available_slots()` rewritten against `AppointmentRequest`
- Admin registrations for AppointmentRequest and RefundQueue
- Verified: `makemigrations --check` clean, `check` 0 issues, `migrate` all passed

### Phase 2: SHEIN-Style Frontend ✅ (Aug 10, 2026)
- E-commerce product detail page built
- Dynamic image gallery with hero + thumbnails
- Option selection (radio cards ≤4, dropdown >4)
- M2M `linked_options` on `ServiceImage`
- Vanilla JS for dynamic image switching
- Discount badge + strikethrough pricing
- Dispatched to hack_3, verified, merged to main4qp

### Phase 2.5: Navigation & i18n ✅ (Aug 10, 2026)
- Navigation cleanup (removed client auth from nav, kept admin login)
- i18n infrastructure setup (`{% trans %}` on all template strings)
- Template `{% trans %}` audit across existing pages
- 14 files modified, 13/13 acceptance criteria verified
- Dispatched to hack_3, verified, merged to main4qp

### Phase 3: Consultation Wizard (Steps 1-2) ✅ (Aug 10, 2026)
- Built 4-step HTMX wizard structure
- Step 1: Service options configuration (radio cards, dropdowns, checkboxes for add-ons)
- Step 2: Provider + schedule date/time (HTMX time slots)
- Steps 3-4: Disabled ("Coming soon")
- Progress indicator: Configure → Schedule → Details → Review
- Session-based state management (`consult_<pk>`)
- Dispatched to hack_3, verified, merged to main4qp

### Phase 4: Wizard Steps 3-4 + Guest Lookup 📋 READY TO DISPATCH (Aug 11, 2026)
**Status:** Analysis complete, architecture decided, ready to dispatch to builders.

**Key Architecture Decision — Draft Approach:**
- `proof_of_payment` model field changed to `blank=True` (safe — no existing AppointmentRequest objects)
- Step 3 submit creates `AppointmentRequest` with `status=pending_verification`, all client data + hair photos. `proof_of_payment` left blank.
- Step 4 updates the existing record with payment method + proof of payment.
- Session stores `appointment_request_id` between steps.
- This avoids temp file storage for multi-step HTMX file uploads.

**Wizard Step 3 — Client Details & Hair Data:**
- Client name, email, phone, age
- Age validation: client-side JS on input change + server-side enforcement on submit
- Hair length selection: 9 visual clickable cards (Ear → Hip)
- Photo uploads: front, side, back with JS thumbnail previews (`URL.createObjectURL`)
- File validation: `.jpg/.jpeg/.png/.webp`, max 5MB, `accept` attribute + JS size check
- Thin hair tension warning (hardcoded text, no checkbox)
- GDPR/Privacy Policy consent checkbox (required)
- Transition to Step 4: Regular form POST with `enctype="multipart/form-data"`

**Wizard Step 4 — Finances & Submission:**
- Display: calculated deposit amount, AFH-XXXXXX reference with copy button, service/provider/date summary
- Payment method selection: radio cards (Revolut, Wise, TransferGo, Bank Transfer)
- Proof of payment upload: `.jpg/.jpeg/.png/.pdf`, max 5MB
- Policy review text + final consent checkbox
- Submit: updates AppointmentRequest, sets `held_until = now + 12 hours`, redirects to confirmation

**Confirmation Page:**
- "Your appointment request has been submitted!"
- Payment reference code (large, copyable)
- Next steps explanation
- Link to Guest Lookup page
- Reference code reminder

**Guest Lookup Page (`/bookings/status/`):**
- Email + AFH reference → status lookup
- Show/hide rules by status (see MASTER_CONTEXT for full spec)
- Admin notes visible to client (transparent — admin writes professionally knowing clients see them)
- Proof of payment images hidden (sensitive bank info)
- Internal notes hidden
- No authentication required

### Phase 4: Wizard Steps 3-4 + Guest Lookup ✅ COMPLETE (Aug 12, 2026)
**Status:** Built, merged to main4qp, end-to-end tested and verified by HICLAW Manager.

**Built by:** hack_3 (Wizard Steps 3-4 + Confirmation) + hack_1 (Guest Lookup)
**Merge commits:** `3269310` (wizard), `ccc97e7` (guest lookup) on main4qp

**Model Changes Applied:**
- `proof_of_payment` → `blank=True`
- `payment_method` → `blank=True`
- Migration `0002_alter_appointmentrequest_payment_method_and_more.py`

**Wizard Step 3 — Client Details & Hair Data (Built ✅):**
- Client name, email, phone, age with age validation (client-side JS + server-side)
- Hair length: radio selection (9 options Ear → Hip)
- Photo uploads: front, side, back with `accept` attribute + file validation
- Thin hair tension warning (hardcoded text)
- GDPR consent checkbox (required)
- Creates `AppointmentRequest` with `status=pending_verification`

**Wizard Step 4 — Finances & Submission (Built ✅):**
- Deposit amount display (20,000 Ft), AFH-XXXXXX reference with copy button
- Payment method radios (Revolut, Wise, TransferGo, Bank Transfer)
- Proof of payment upload (.jpg/.png/.pdf, max 5MB)
- Policy review text + final consent checkbox
- Updates `AppointmentRequest`, sets `held_until = now + 12h`

**Confirmation Page (Built ✅):**
- Success message, large copyable reference, next steps, Guest Lookup link

**Guest Lookup Page (Built ✅):**
- Email + AFH reference → status lookup (case-insensitive)
- HTMX form submission with partial result swap
- Show/hide rules per Decision #15 — verified for pending_verification status
- Proof of payment images + internal notes hidden ✅
- Admin notes visible for appropriate statuses ✅
- Error handling for invalid lookups ✅

**End-to-End Test (Aug 12):**
- Full flow tested: Homepage → Detail → Step 1 (options) → Step 2 (scheduling) → Step 3 (details + photos) → Step 4 (payment + proof) → Confirmation → Guest Lookup
- All data persisted correctly: reference AFH-BCECE7, status pending_verification, frozen options snapshot, all photos/proof stored, 12h hold set
- `manage.py check` = 0 issues, `makemigrations --check` = clean

**Known Cosmetic Issues (not blocking):**
1. `---------` blank option in radio groups (hair_length, payment_method) — Django ChoiceField default empty label. Remove in polish phase.
2. Double navigation/footer on Steps 3-4 pages — they extend base.html but also render wizard shell. Fix template inheritance in polish phase.
3. "Coming soon" labels in wizard shell progress bar for Steps 3-4 — the step 3/4 pages show correct progress, but the wizard shell (steps 1-2) still says "Coming soon". Fix in polish phase.

---

## Current Codebase State

| App | Status | Notes |
|-----|--------|-------|
| `services` | ✅ Complete | Suitability fields, M2M images, SHEIN detail page, discount engine, `request.seo_service` (7E) |
| `bookings` | ✅ Functional | AppointmentRequest model, wizard Steps 1-4, confirmation, guest lookup, admin review workflow, auto-expire command, dynamic payment methods + snapshots (7B), `customer_language` persistence (7B) |
| `payments` | 🗑️ Decommissioned | Dead weight removed in Phase 0 |
| `providers` | ✅ Stable | Stylists + weekly availability |
| `site_config` | ✅ Complete | Singleton config (7A), FAQ/ContentBlock/Announcement (7D), EmailTemplate system (7C), SEO config (7E), context processors |
| `users` | ✅ Stable | Custom user model |
| `reviews` | ❌ Deleted | Intentionally scrapped |

## Branches

- `main` — production
- `main4qp` — integration branch (all feature branches merge here first)
- Stale feature branches (Phase 2, 2.5, 3) — fully merged, safe to delete

## Dev Environment

- **Python:** 3.12.12
- **Django:** 4.2.25
- **Database:** SQLite (dev)
- **Venv:** `.venv`
- **Superuser:** admin / admin123
- **Local path:** `C:\Users\Sabiedu\Projects\afrikai-hajfonas`

---

### Phase 5: Admin Dashboard ✅ COMPLETE (Aug 12, 2026)
**Status:** Built, merged to main4qp, tested and verified by HICLAW Manager.
**Merge commit:** `dd4d78d` → merged to main4qp

**Built by:** HICLAW Manager (direct build — deeply interconnected admin work)

**1. Custom Admin Dashboard (templates/admin/index.html + config/admin_dashboard.py):**
- Operational dashboard replacing Django's default admin index
- Widgets: Pending Deposit Verification, Pending Photo Review, Expiring Soon (2h), Today's Confirmed, Refund Queue, Approved Deposit Revenue
- Urgent "Expiring Soon" table, Today's Schedule table, Pending Action Queue table
- Quick action buttons to all admin sections + public site
- AdminSite.index patched at class level (clean, no custom AdminSite subclass needed)

**2. Appointment Review Workflow (apps/bookings/admin.py):**
- Custom fieldsets with emoji headers for daily review flow
- Inline photo previews (front/side/back) in change view
- Proof of payment: images inline, PDFs as clickable link
- Color-coded status badges + live hold timer with urgency coloring
- Admin actions: Approve, Reject (→Refund Queue), Verify Payment (→Pending Review)

**3. Auto-Expire Management Command (expire_holds.py):**
- Finds requests past 12-hour hold window, marks as expired
- --dry-run flag, admin email notification, cron-ready

**4. Seasonal Discount (apps/services/admin.py):**
- list_editable discount_percentage, bulk apply/clear actions, display column

**Known Limitation — Dynamic M2M Admin Form:**
- Grouped option dropdowns require StackedInline (TabularInline can't render dynamic fields)
- linked_options editable via individual ServiceImage change form
- Code preserved in git history for future activation

---

## What's Left After Phase 5

- ~~**Phase 6:** Background tasks + polish~~ ✅ (see below)
- ~~**Dynamic M2M Form:** Switch ServiceImage inline to StackedInline~~ ✅
- ~~**Final Polish:** Static pages, language preference popup~~ ✅

---

### Phase 6: Polish, i18n, Static Pages ✅ COMPLETE (Aug 12, 2026)
**Status:** Built, merged to main4qp, all pushed.
**Branch:** `main4qp` @ `c4dc9db`

**Track A — Expiry Reminder Emails ✅ (built by hack_1):**
- `AppointmentRequest` model: `reminder_2h_sent` / `reminder_1h_sent` BooleanFields
- Migration `0003_appointmentrequest_reminder_1h_sent_and_more`
- `send_expiry_reminders` command: idempotent, `--dry-run`, 2h/1h windows
- `expiry_reminder.txt` email template
- E2E tested. Commit `242036e`.

**Track B — Static Pages ✅ (built by hack_3):**
- 4 pages: About (`/about/`), Contact (`/contact/`), Terms (`/terms/`), Privacy (`/privacy/`)
- Views in `apps/site_config/views.py`, routes in `config/urls.py`
- `href="#"` placeholder links replaced with real `{% url %}` tags
- All strings wrapped in `{% trans %}`. Commits `e7c9437`, `ee79c9b`, `5be51e9`.

**Track C — i18n Translations ✅ (built by HICLAW Manager):**
- polib-based i18n workflow (no GNU gettext needed on Windows)
- 323 strings extracted from templates + Python code
- **HU: 323/323**, **DE: 323/323**, **EN: 323/323** (969 total)
- Language preference popup (JS modal + Django i18n cookie, first-time visitors)
- Mobile language switcher added to mobile menu
- `save_as_mofile()` bug fixed (was using `save()` which writes .po format)
- Commits: `3fbba49`, `7424508`, `f8d3c79`, `b8db076`, `c4dc9db`

**Track D — UI Polish ✅ (built by HICLAW Manager):**
- `WizardStep3Form` / `WizardStep4Form`: explicit `.choices` to remove blank `---------` options
- Wizard progress bar: replaced stale "coming soon" 4-step bar with shared `wizard_progress.html`
- Commit `c6abddd`.

**Track E — Admin StackedInline ✅ (built by HICLAW Manager):**
- `ServiceImageInline` → `StackedInline`
- `DynamicServiceImageForm`: per-ServiceOption-group `<select>` dropdowns
- `image_preview` read-only field for visual confirmation
- Commit `0f8da37`.

---

## Phase 7: Business-Managed Content & Configuration ✅ COMPLETE (Aug 12, 2026)
**Principle Document:** `specs/ARCHITECTURAL_PRINCIPLES.md` (Rev 3)
**Goal:** Move all business-owned content and configuration from code/templates into Django Admin.
**Integration Branch:** `main4qp` @ `865b797` (all tracks merged, pushed)

### Cross-Cutting Requirements (All Complete ✅)
- [x] **Three Content Categories documented** — A (dev UI `{% trans %}`), B (admin reusable parent+translation DB records), C (appointment-specific, no translation). Decision #26.
- [x] **Multilingual content strategy** — parent + `Translation` records for all Category B content (FAQ, ContentBlock, EmailTemplate, SEO, Announcement). NOT `{% trans %}` for DB content.
- [x] **Appointment language persistence** — `AppointmentRequest.customer_language` (hu/en/de), captured at Step 3 submit via `get_language()[:2]`, immutable. Decision #28.
- [x] **Shared `LanguageChoices` enum** in `apps/site_config/constants.py`.

### Phase 7A: Business Information Expansion ✅ (commit `1b103c0`)
- [x] Extend `SiteConfiguration` with: business_name, logo, favicon, hero_title/subtitle/image, address_description, business_hours, google_maps_link, website_url
- [x] Admin: `SingletonModelAdmin` with grouped fieldsets
- [x] Templates: `base.html` uses `{{ config.* }}` for business name, logo, favicon, hero
- [x] Global SEO fields deferred to Phase 7E (dedicated `GlobalSEO` model)
- [x] Migration: `0002_siteconfiguration_expansion` (7A fields)

### Phase 7B: Dynamic Payment Methods + Historical Snapshots ✅ (merge `ca3d886`)
- [x] `PaymentMethod` model (admin-managed, replaces TextChoices)
- [x] `PaymentDetailField` model (6 field types: text, textarea, number, email, url, image)
- [x] `AppointmentPaymentSnapshot` model (frozen payment config per appointment)
- [x] Seed migration: 4 methods (Revolut, Wise, TransferGo, Bank Transfer) + detail fields
- [x] `customer_language` on `AppointmentRequest` (migration + default `hu`)
- [x] Data migration: TextChoices → FK mapping
- [x] `create_payment_snapshot()` at Step 4 submission — same transaction, with image file physical copy to `payment_snapshots/<ref>/` (Decision #32)
- [x] `payment_method_fk` uses `on_delete=SET_NULL` (survives method deletion)
- [x] **Step 4 UI**: dynamic payment method cards (radio) + HTMX detail fields display (`payment_detail_fields` endpoint + `_payment_detail_fields.html` partial)
- [x] **Guest Lookup: reads ONLY `payment_method_name` from snapshot** — detail fields are admin-only audit (Decision #31)
- [x] Admin: `PaymentMethodAdmin` + `PaymentDetailFieldInline`, snapshot read-only inline, `language_flag` display (🇭🇺/🇬🇧/🇩🇪)
- [x] `payment_method` → `payment_method_fk` replaced everywhere (views, admin, forms, RefundQueueAdmin)
- [x] Migrations 0004-0007 (models + seed + data migration + fix)

### Phase 7C: Editable Email Templates — Infrastructure ✅ / Triggers Partial (merge `854ca3c`)
- [x] `EmailTemplate` model (8 developer-controlled email types, `is_active` toggle)
- [x] `EmailTemplateTranslation` model (subject + body_text + optional body_html, `unique_together`)
- [x] `email_service.py`: `render_text()` (regex `{{ key }}` substitution — NOT Django template engine, Decision #34), `render_email()` (language fallback: requested → HU), `find_unknown_placeholders()` / `find_placeholders()`, `EMAIL_PLACEHOLDERS` (31 canonical keys)
- [x] Admin: `EmailTemplateTranslationForm` (ModelForm + field-level `clean_*` validates placeholders), `EmailTemplateTranslationInline`, `EmailTemplateAdmin`
- [x] Seed migration: 8 types × 3 languages = 24 translations (HU/EN/DE)
- [x] `body_text` = plain textarea, `body_html` = optional plain HTML textarea (**NO WYSIWYG for emails**)
- [x] Transactional vs newsletter strictly separate (Decision #29)
- [x] `send_expiry_reminders` command refactored to use `render_email()` with legacy template fallback
- [x] Migrations 0006-0007

**⚠️ Email Trigger Status (7 of 8 types have no code trigger):**

| Email Type | Template Seeded | Code Trigger | Status |
|---|---|---|---|
| `expiry_reminder` | ✅ | ✅ `send_expiry_reminders` command (`render_email()` + legacy fallback) | **ACTIVE** |
| `request_received` | ✅ | ❌ No trigger in Step 3 submit view | **FUTURE WORK** |
| `verification_pending` | ✅ | ❌ No trigger in Step 4 submit view | **FUTURE WORK** |
| `payment_verified` | ✅ | ❌ `verify_payments` admin action sends no email | **FUTURE WORK** |
| `appointment_approved` | ✅ | ❌ `approve_requests` admin action sends no email | **FUTURE WORK** |
| `appointment_rejected` | ✅ | ❌ `reject_requests` admin action sends no email | **FUTURE WORK** |
| `appointment_expired` | ✅ | ❌ `expire_holds` sends raw `mail_admins()` (admin notification only, not template-based, not customer-facing) | **FUTURE WORK** |
| `refund_notification` | ✅ | ❌ `complete_refunds` admin action sends no email | **FUTURE WORK** |

> **Note:** Phase 7C's deliverable per spec §7 was the email infrastructure (models, rendering service, placeholder validation, seed data). The spec assigns trigger logic to the developer ("Email-sending logic (when/where/trigger)"). The trigger wiring is a separate implementation step — the templates and rendering pipeline are ready; the `send_mail` calls in views/admin actions are not yet added.

### Phase 7D: Customer-Facing Content ✅ (merge in `0a68461`)
- [x] `FAQ` + `FAQTranslation` (question, answer per language)
- [x] `ContentBlock` + `ContentBlockTranslation` (title, body by slug)
- [x] `Announcement` + `AnnouncementTranslation` (message, link, scheduling)
- [x] WYSIWYG: `django-summernote` (limited toolbar) + `bleach` sanitization (Decision #33)
- [x] Template tags: `{% get_content_block %}`, `{% get_faqs %}` with language fallback to HU
- [x] Static page integration: `about_page`, `terms_page`, `privacy_page` ContentBlocks wired into page templates with hardcoded `{% trans %}` fallback
- [x] Admin: `StackedInline` for all translation models, `SummernoteWidget` on body/answer fields
- [x] Seed data: FAQ items, ContentBlocks, Announcement
- [x] Migrations 0004-0005

**⚠️ Partial — Static Page Prose Migration (spec §8.4):**
Only the main prose sections of About/Terms/Privacy use ContentBlocks with fallback. Other page sections (Our Mission, Values, Team, Trust badges on About page) remain hardcoded `{% trans %}`. The spec says "Body text, policy text, about text" should move — the main body text did. Full migration of all page prose is polish work.

### Phase 7E: SEO Configuration ✅ (merge `865b797`)
- [x] `GlobalSEO` (SingletonModel): canonical_site_url, og_image_default, google_verification, bing_verification
- [x] `GlobalSEOTranslation`: default_meta_title, default_meta_description, default_og_title, default_og_description (`unique_together`)
- [x] `PageSEO`: url_path (static) OR service OneToOne (dynamic), is_active, CheckConstraint (`pageseo_exactly_one_target`) + Python `clean()` enforcement
- [x] `PageSEOTranslation`: meta_title, meta_description, og_title, og_description (`unique_together`)
- [x] `seo_service.py`: `resolve_seo()` with 3-tier fallback chain (Page-level → Global default → Hardcoded dev `_DEV_FALLBACK`), language fallback (requested → HU)
- [x] Context processor: `seo()` registered in settings, auto-resolves via `request.path`; views can set `request.seo_service`
- [x] `base.html`: `<title>`, meta description, canonical link, OG tags, Google/Bing verification — all driven by `{{ seo.* }}`
- [x] Service detail view sets `request.seo_service` for per-service SEO
- [x] Seed migration: GlobalSEO singleton + HU defaults + 6 static PageSEO (`/`, `/about/`, `/contact/`, `/terms/`, `/privacy/`, `/services/`)
- [x] Admin: `GlobalSEOAdmin` (SingletonModelAdmin) + `PageSEOAdmin` with translation inlines
- [x] Migrations 0008-0010

**⚠️ Not built (legitimately deferred — developer-managed per spec §9.5):**
- `sitemap.xml`, `robots.txt`, `hreflang`, JSON-LD structured data — all developer-managed technical SEO, not admin-configurable. Not part of Phase 7E scope.
- `/consult/` PageSEO — the wizard URL is dynamic (`/bookings/book/<service_pk>/`), not a static route. No static PageSEO created for it (documented spec/URL mismatch).

---

### Phase 7 Test Suite
**74 tests collected, 69 passed, 5 skipped** (all in `apps/site_config/tests.py`; other app test files are empty stubs).

The 5 skipped tests are all Service-dependent SEO tests that skip because no `Service` fixture exists in the test database:
- `PageSEOConstraintTests::test_service_only_allowed`
- `PageSEOConstraintTests::test_both_set_rejected_by_clean`
- `PageSEOConstraintTests::test_service_only_passes_clean`
- `ResolveSEOServiceTests::test_service_seo_resolution`
- `ResolveSEOServiceTests::test_service_without_seo_falls_back`

> ⚠️ The commit message for Phase 7E claimed "74 tests all passing" — this was **inaccurate**. Correct count is 69 passed, 5 skipped.

Test breakdown by track:
- **7D** (SanitizeHtml, FAQ/ContentBlock/Announcement models, template tags, seed): ~20 tests
- **7C** (render_text, render_email, placeholder validation, admin form validation, seed integrity): ~33 tests
- **7E** (SEO seed verification, PageSEO constraint/clean, resolve_seo fallback chain, service SEO): ~21 tests (5 skipped)

---

## Session Management Policy (for HICLAW)

**Context windows fill up.** When working on a long project like this, sessions accumulate context. Here's the policy:

- If your context window is getting full (above ~70%), start a fresh session for the next phase.
- The specs are in the repo — re-read them in the new session.
- Don't force through a big phase on a half-full context — quality degrades.
- Starting fresh is NOT failure. It's good practice.
- Each new session should re-read: this file (PROGRESS_HISTORY.md), MASTER_CONTEXT_AND_SPECS.md, and DECISIONS.md.
