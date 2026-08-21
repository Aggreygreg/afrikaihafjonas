# Afrikai Hajfonás — Progress History

**Last Updated:** August 21, 2026

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

### Phase 4: Wizard Steps 3-4 + Guest Lookup — Planning (Aug 11, 2026)
**Status:** ✅ Built and merged — see the "COMPLETE" entry below. This section preserves the original architectural plan.

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

- `main` — **production branch and the new default target** (all Phase 1–7 work merged Aug 17, 2026, commit `ef16dc7`)
- `main4qp` — former integration branch; fully merged into `main`, retained for history only
- All Phase 1–7 feature branches deleted (local + remote) after ancestor-verified merges

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

### Phase 7C: Editable Email Templates — ✅ Complete (merge `854ca3c` + commit `6fafc51`)
- [x] `EmailTemplate` model (8 developer-controlled email types, `is_active` toggle)
- [x] `EmailTemplateTranslation` model (subject + body_text + optional body_html, `unique_together`)
- [x] `email_service.py`: `render_text()` (regex `{{ key }}` substitution — NOT Django template engine, Decision #34), `render_email()` (language fallback: requested → HU), `find_unknown_placeholders()` / `find_placeholders()`, `EMAIL_PLACEHOLDERS` (31 canonical keys)
- [x] Admin: `EmailTemplateTranslationForm` (ModelForm + field-level `clean_*` validates placeholders), `EmailTemplateTranslationInline`, `EmailTemplateAdmin`
- [x] Seed migration: 8 types × 3 languages = 24 translations (HU/EN/DE)
- [x] `body_text` = plain textarea, `body_html` = optional plain HTML textarea (**NO WYSIWYG for emails**)
- [x] Transactional vs newsletter strictly separate (Decision #29)
- [x] `send_expiry_reminders` command refactored to use `render_email()` with legacy template fallback
- [x] Migrations 0006-0007
- [x] **`notifications.py`** — `send_appointment_email(appointment, email_type, request=None)` module with `_build_context()` (31 canonical keys), `_build_absolute_url()`, `_format_selected_options()`. Uses `appointment.customer_language` for language selection. `request` optional (management commands fall back to `SiteConfiguration.website_url + reverse()`).
- [x] **All 8 email triggers wired** (commit `6fafc51`)

**✅ Email Trigger Status (8/8 ACTIVE):**

| Email Type | Template Seeded | Code Trigger | Status |
|---|---|---|---|
| `expiry_reminder` | ✅ | ✅ `send_expiry_reminders` command (`render_email()` + legacy fallback) | **ACTIVE** |
| `request_received` | ✅ | ✅ `wizard_step_3` view (POST success) | **ACTIVE** |
| `verification_pending` | ✅ | ✅ `wizard_step_4` view (snapshot created) | **ACTIVE** |
| `payment_verified` | ✅ | ✅ `verify_payments` admin action | **ACTIVE** |
| `appointment_approved` | ✅ | ✅ `approve_requests` admin action | **ACTIVE** |
| `appointment_rejected` | ✅ | ✅ `reject_requests` admin action | **ACTIVE** |
| `appointment_expired` | ✅ | ✅ `expire_holds` command | **ACTIVE** |
| `refund_notification` | ✅ | ✅ `complete_refunds` admin action | **ACTIVE** |

**Tests:** 18 notification tests in `apps/bookings/tests.py` (`NotificationTests` + `NotificationEdgeCaseTests`) — context building, all trigger paths, language selection, graceful failures, inactive templates. Total suite: **92 passed, 0 skipped**.

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

**Static Page Prose Migration (§8.4) — ✅ Complete:**
- All main body content on About/Terms/Privacy uses ContentBlock with `{% trans %}` fallback
- About page "Our Mission" prose migrated to `about_mission` ContentBlock (migration `0011`)
- Values cards, Team section (TODO for dynamic Provider data), Trust badges remain `{% trans %}` — these are structural UI elements, not admin-editable prose

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

**⚠️ Technical SEO (§9.5) — implemented as developer-managed code:**
- [x] `sitemap.xml` — Django sitemap framework: `StaticViewSitemap` (6 static pages) + `ServiceSitemap` (dynamic, all services). Sitemap index at `/sitemap.xml`, sections at `/sitemap-<section>.xml`.
- [x] `robots.txt` — served at `/robots.txt`, allows all crawlers, disallows `/admin/`, `/bookings/book/`, `/bookings/status/`, `/summernote/`. References sitemap.
- [x] JSON-LD `HairSalon` structured data — built in `context_processors._build_jsonld_localbusiness()` from `SiteConfiguration` singleton (name, phone, email, address, map, hours, social links). Rendered on every page via `base.html`.
- [x] Canonical tag logic — already implemented in Phase 7E (`seo.canonical_url` + `request.path`).
- [x] 6 tests in `config/tests.py` (sitemap index, static section, services section, robots.txt content, JSON-LD rendering, JSON-LD field omission).
- **hreflang intentionally NOT implemented:** The site uses cookie/session-based language switching (LocaleMiddleware), not i18n URL patterns (`/en/`, `/de/`). Without distinct URLs per language, hreflang annotations are meaningless to search engines. Implementing hreflang would require switching to `i18n_patterns`, which is a significant architectural change that would alter all existing URLs and the language popup logic. Documented as a future enhancement if URL-based i18n is adopted.

---

### Phase 7 Test Suite
**98 tests collected, 98 passed, 0 skipped** across `config/tests.py`, `apps/site_config/tests.py`, and `apps/bookings/tests.py`.

Test breakdown by module:
- **config/tests.py**: 6 tests — Technical SEO (sitemap index/sections, robots.txt, JSON-LD LocalBusiness) ✅ NEW
- **apps/site_config/tests.py**: 74 tests — SanitizeHtml, FAQ/ContentBlock/Announcement models, template tags, render_text/render_email, placeholder validation, admin form validation, seed integrity, SEO seed verification, PageSEO constraint/clean, resolve_seo fallback chain, service SEO ✅ ALL PASSING (previously 5 skipped — fixed with Service fixtures)
- **apps/bookings/tests.py**: 18 tests — Notification system (context building, all 8 trigger paths, language selection, graceful failures, inactive templates) ✅ ALL PASSING

---

### Production Hardening ✅ COMPLETE (Aug 13, 2026)
**Status:** Production-readiness audit + end-to-end smoke testing + critical bug fix. All on `main4qp`, pushed.
**Commits:** `45f558b`, `0373c0b`, `9716a79`

**1. Production Security Settings (`45f558b`):**
- `SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS` parsing hardened (no None crash, no empty-string)
- `STATIC_ROOT = BASE_DIR / "staticfiles"` added
- Email backend fully env-configurable (SMTP for prod, console for dev)
- `CSRF_TRUSTED_ORIGINS` configurable for HTTPS production domain
- Production security block activates when `DEBUG=False`: HSTS, secure cookies, content type nosniff, referrer policy, proxy SSL header
- `SECURE_SSL_REDIRECT` env-configurable (default True; set False if CDN handles edge redirect)
- `.env.example` — complete deployment env var reference
- `specs/DEPLOYMENT.md` — 7-step deployment guide + nginx config + cron jobs + troubleshooting
- `.gitignore` — `staticfiles/`, `mediafiles/`, `server_log.txt` added; `.env.example` un-ignored
- `requirements.txt` recompiled: `bleach` + `django-summernote` were missing (fresh install would crash)

**2. End-to-End Smoke Testing (DEBUG=False + Real SMTP):**
- Full customer journey tested: Homepage → Service Detail → Wizard Steps 1-4 → Confirmation → Guest Lookup
- All 4 admin workflows tested: verify payment → approve → reject → complete refund
- Both management commands tested: `expire_holds`, `send_expiry_reminders` (2h + 1h)
- All 8 email triggers verified via SMTP capture (correct language, correct content)
- Security headers verified active: X-Frame-Options DENY, nosniff, Referrer-Policy, secure cookies
- Guest Lookup verified: valid lookup returns correct details; invalid lookup shows styled error; bank details NEVER shown to customers (Decision #15/#31 respected)
- Media file serving: 404 via Django in DEBUG=False (correct — nginx serves `/media/` in production)

**3. Critical Bug Found & Fixed During Smoke Test (`0373c0b`):**
- **Step 4 payment selector non-functional:** `WizardStep4Form.payment_method_fk` used the default `Select` widget, which rendered `<option>` tags. The template iterated choices expecting `<input type="radio">`, making the entire payment step unselectable.
- **Fix:** Changed to `forms.RadioSelect(attrs={"class": "sr-only peer"})`. Widget must be set BEFORE queryset assignment so choices propagate correctly.
- Re-tested: radio buttons render correctly (4 methods), HTMX detail fields load, proof upload works, submission succeeds.

**4. PostgreSQL Compatibility (Code Review):**
- No raw SQL, no `.raw()` queries, no `connection.cursor()`, no SQLite-specific code
- `JSONField` maps to `jsonb` on PostgreSQL (cross-database compatible)
- `CheckConstraint` uses standard `models.Q` (cross-database compatible)

**Verification:**
- `check --deploy`: 0 issues (with proper-length SECRET_KEY)
- `collectstatic`: 195 files collected successfully
- 98 tests passed, 0 skipped, 0 failed
- `makemigrations --check`: clean
- 47/47 migrations applied, 0 pending *(original note said 49 — corrected by the Phase 8 migration-integrity audit; see below)*

**Intentionally Deferred Limitations:**
- PostgreSQL live instance: not tested locally (no PG installed), but code review confirms compatibility
- Real HTTPS/TLS: not tested (no cert locally), but security headers + HSTS config verified
- hreflang: not implemented (cookie/session-based i18n, not URL prefixes — requires `i18n_patterns` architectural change)

---

## Phase 8: Merge to main + Documentation Sync ✅ COMPLETE (Aug 17, 2026)

**1. Spec Audit on `main4qp` (commit `a90ded9`):** MASTER_CONTEXT / DECISIONS #24 / DEPLOYMENT / EXECUTION_RULES #20 / PROGRESS_HISTORY aligned to production-ready reality (payment_method_fk snapshot, gettext-optional note, flat upload paths, Production Hardening entry).

**2. Branch Cleanup:** after ancestor checks, deleted merged feature branches locally + on origin (`feature/consult-wizard`, `feature/i18n-nav-cleanup`, `feature/shein-detail-page`, remote-only `feature/static-pages`). Remaining: `main`, `main4qp`.

**3. Merge `main4qp` → `main` (commit `ef16dc7`, --no-ff):** 108 files, ~17.9k insertions. Verified on `main`: 98/98 tests, 0 pending migrations, clean tree.

**4. Migration-Integrity Audit — SAFE:**
- Canonical applied-migration count is **47** (`showmigrations --plan` + `django_migrations` table agree)
- The historical "49" included the two `payments` migrations deleted at decommission commit `e2687c8` (app left as empty shell, removed from `INSTALLED_APPS`)
- Fresh-DB test (`DATABASE_URL=sqlite:///db_fresh_test.sqlite3`): migrate-from-zero = 47/47 OK, seeds verified (PaymentMethod 4, PaymentDetailField 9, ContentBlock 4, EmailTemplate 8, GlobalSEO 1), `makemigrations --check` clean, 98/98 tests; test DB deleted

**5. Documentation Sync on `main` (this commit):** full README rewrite (was 2 lines) + specs aligned with actual code:
- Language modal: `django_language` cookie + `/i18n/setlang/` POST (no localStorage, no URL prefixes)
- URL map: real routes incl. `/bookings/book/<pk>/` (no `/consult/`), ajax endpoints, sitemap/robots
- site_config section: Phase 7 models documented as built; payments decommission note + migration-count clarification
- Branching section: `main` is now the default target; `main4qp` historical
- Known issues documented (NOT fixed — out of scope for a docs commit):
  1. ~~`service_list.html` HTMX script missing~~ → **FIXED Aug 18, 2026** (see Post-Merge Fixes below)
  2. No public FAQ page (models + admin exist; nav links are `#faq`/`#` placeholders)
  3. `SECURE_REDIRECT_EXEMPT` references non-existent `/health-check/` route (dead config)
  4. `Dockerfile` is a stub (no pip install/CMD) — venv flow is the supported setup
  5. Legacy `media/` directory at repo root (real `MEDIA_ROOT` = `mediafiles/`)

---

## Post-Merge Fixes

### HTMX Catalog Fix ✅ (Aug 18, 2026)
**Bug:** `service_list.html` used `hx-get`/`hx-trigger` and called `htmx.trigger()` without loading the HTMX runtime (only `consult_wizard.html` loaded it) — gender tabs threw `htmx is not defined`, debounced search was inert; only the native form submit worked.

**Fix:** added the per-template include `<script src="https://unpkg.com/htmx.org@1.9.12" defer>` (same pattern as the wizard; base template intentionally stays script-free). Root cause verified end-to-end before fixing: view already had the `HX-Request` → `service_grid.html` partial switch whose root `#services-wrapper` matches `hx-target`/`hx-swap=outerHTML`.

**Verification:** live browser test — htmx 1.9.12 present; gender tab click fired `GET /services/?gender=…` (200) with full swap chain (`beforeRequest → beforeSwap shouldSwap=true → afterSwap`); debounced search (`q=knotless`) fired + swapped; native full-page GET with filter params still renders the complete page with "Apply Filters" (no-JS fallback intact). Added `apps/services/tests.py` (was an empty stub): 4 regression tests. Suite: 102/102. `makemigrations --check` clean.

**Discovered during verification (NOT fixed — separate authorization required):**
- `service_list_view` gender lookup uses `name__icontains` → "Women's Braids" contains "men's braids", so the **Men's tab matches the Women's parent** (`.first()` order-dependent). Affects HTMX and native fallback alike. Proposed fix: `name__iexact`.
- Cosmetic: gender tab pill highlight doesn't update after an HTMX swap (tabs render outside the swapped `#services-wrapper`).
- The dev-DB 404s during testing were `/media/service_images/test_0.jpg` — the legacy-media known issue (#5), unrelated.

---

### Dynamic ParentCategory Tabs ✅ (Aug 18, 2026 — branch `feature/dynamic-parent-categories`, NOT yet merged)
**Change:** `/services/` top-level tabs are generated from `ParentCategory` records instead of hardcoded Women's/Men's/Children's buttons. Admin-created categories appear automatically as tabs. Selection is ID-based (`?cat=<pk>`); the old `gender` name param and its buggy `name__icontains` lookup (the "Men's tab matches Women's" substring bug above) were removed. This deliberately supersedes the "exactly three entries" model rule — full scope, rejected alternatives (`sort_order`/`is_active` fields, Category B translations, color management), and the translation consequence are recorded in **Decision #35**.

**Deliberately out of scope (deferred, not requirements):** category landing URLs/slugs/SEO, category images, multilingual category names, `sort_order`/`is_active` model fields.

**Files:** `apps/services/views.py` (ID-based `cat` param, creation-order tabs, safe fallbacks), `templates/services/service_list.html` (dynamic tab loop, `cat` hidden input, `switchCategory()` with highlight sync — also fixes the stale-highlight cosmetic issue), `apps/services/tests.py` (rewritten: 25 tests covering tab rendering, auto-appearance of admin-created categories, per-category filtering, substring-collision regression, sidebar scoping, search/sort/price, empty/no-category cases, admin CRUD incl. rename/delete, HTMX partial + native fallback). Plus spec sync: MASTER_CONTEXT, DECISIONS (#4 update, #35 new), EXECUTION_RULES gotchas, this file, README.

**Verification:** baseline 102/102 → **123/123**; `makemigrations --check` clean (**no schema change — no migration**); `manage.py check` 0 issues; `.po` files untouched (no new msgids; removed 3 dead `{% trans %}` wrappers whose msgids never existed). Live browser: 4 tabs incl. admin-created "Bridal" rendered from DB; Men's tab click → HTMX swap, highlight moves, women's service absent (bug dead); per-category sidebar scoping; native `?cat=3` full-page fallback; debounced search intact. Dev DB seeded additively (idempotent `get_or_create`) with Men's/Children's/Bridal parents + demo services for acceptance testing.


---

## Public FAQ Page + Announcement Rendering + Cleanup ✅ (Aug 19, 2026 — branch `feature/public-faq-site-content`, NOT yet merged)

**Goal:** Close three documented gaps from the prior-cycle audit — (1) `FAQ` model had no public page; (2) `Announcement` model was never rendered; (3) scaffold-era dead artifacts (`Dockerfile`, `docker-compose.yml`, `SECURE_REDIRECT_EXEMPT` health-check line, legacy `media/` dir, broken `ServiceImage` rows) persisted. Plus the final UI/UX visual QA pass. Full scope/rejected-alternatives in **Decision #36**.

**36a — FAQ topics + public `/faq/` page (Category B):** New `FAQTopic` + `FAQTopicTranslation`; `FAQ.topic` nullable FK (`SET_NULL`). `faq_page` view groups active FAQs by active topic (display order), ungrouped → final "General" section, HU fallback, HTMX live search (question + `strip_tags(answer)` substring, 400ms debounce, `#faq-list` outerHTML swap) with native GET fallback, empty + no-results states. Templates `pages/faq.html` + `pages/partials/faq_list.html` (`<details>` accordion + expand/collapse-all). Sitemap + 3 nav links (`{% url 'faq' %}`). Admin `FAQTopicAdmin` (inline ×3) + topic on `FAQAdmin`. Migration `site_config/0012_faq_topics`.

**36b — Announcement banner rendering:** Existing `Announcement`/`AnnouncementTranslation` now rendered. `get_active_announcements` tag (active + scheduling window + display order + per-language HU fallback + skip-no-translation). `base.html` banner stack above header; `is_dismissible` → client-side localStorage (slug-keyed, no server round-trip). `message` is plain `CharField` (not WYSIWYG) → `{{ message }}` auto-escaping is the correct safe contract.

**36c — Multilingual admin-content architecture verified:** `FAQ`/`FAQTopic`/`ContentBlock`/`Announcement`/`EmailTemplate`/SEO all confirmed on the parent + per-language translation pattern. No `{% trans %}` for DB-managed business content. Live EN/DE fallback verified.

**36d — Dead artifact cleanup:** `Dockerfile` + `docker-compose.yml` removed (never functional — scaffold at `4c73354`); `SECURE_REDIRECT_EXEMPT` health-check line removed (no consumer); legacy `media/` dir removed + 4 dev `ServiceImage` rows repointed to real tracked files in `mediafiles/` (dev/demo data only — no production ownership claimed). DEPLOYMENT.md had zero Docker refs → no change.

**36e — Mobile visual defects (final UI/UX QA):** (1) Catalog `/services/` parent-category pill bar overflowed 16px @375px → `max-w-full overflow-x-auto` bar + `whitespace-nowrap shrink-0` pills (SHEIN-style scroll bar; desktop unchanged). (2) Info-page hero `<h1>` overflowed 55px @375px on long DE/HU words ("Datenschutzerklärung") → `break-words` on all 5 hero h1s (about/contact/faq/privacy/terms; activates only when a word would overflow).

**36f — Generic CMS / information-page architecture: evaluated, intentionally deferred.** Final information-content audit confirms the existing smallest-appropriate-architecture is sufficient (ContentBlock for long-form, FAQ+topic for knowledge, specialized models for structured business data, Announcement for temporary notices). No generic CMS / reusable "topic page" abstraction introduced — no current spec requires it; deferred until a proven requirement.

**Test-count clarification (no historical record altered):** Decision #35's "102 → 123" is **correct** (74 site_config + 25 services + 18 bookings + 6 config = 123; `providers`/`users`/`payments` are empty stubs). An earlier internal note misread a 3-app partial count (117, omitting `config/tests.py`) as the "real baseline" and labelled 123 an overcount — that was wrong. 123 stands uncorrected.

**Files:** `apps/site_config/` (models, admin, views, templatetags, tests), `config/` (settings, sitemaps, urls), 3× `.po` (+18 msgids each → 341/341 ×3 compiled), `templates/base.html` + 5 info-page h1s + `service_list.html`, new `templates/pages/faq.html` + `partials/faq_list.html`, new migration `0012_faq_topics`. Plus spec sync: README, MASTER_CONTEXT, ARCHITECTURAL_PRINCIPLES §8.1, DECISIONS (#36), EXECUTION_RULES, this file.

**Verification:** baseline 123/123 → **167/167** (44 new site_config tests + `config/tests.py` always had 6 but the documented command previously omitted its path); `makemigrations --check` clean; `manage.py check` 0 issues; **fresh-DB migrate clean** (backup → delete → `migrate --noinput` → all 12 site_config migrations apply incl `0012_faq_topics` → 4 FAQ tables confirmed → dev DB restored); 48 applied migrations. Live acceptance: FAQ topics ordered/grouped, inactive excluded, EN→HU + DE→HU fallback, HTMX partial search (no reload, filter accurate, input retained), no-results state, `<script>`/SQL injection probes all fail safe; banner scheduling window + future-exclusion + HTML-escape safe + dismiss + localStorage persistence across reload. Visual QA desktop 1280×800 + mobile 375×667 across homepage/catalog/SHEIN gallery/info pages/FAQ/wizard/guest-lookup → 2 defects found & fixed (36e). All acceptance test content purged (FAQ/Topic/Announcement → 0/0/0); empty state verified. All temp artifacts removed.

---

## Full Customer-Facing Multilingual ✅ COMPLETE (Aug 20, 2026 — Decisions #38–#40)

**Decision #38 — catalog multilingual (commit `089b122`):** Greg superseded Decision #35 (which had kept the catalog single-language). ALL customer-facing catalog content moved to the parent + Translation pattern (Category B): 7 new Translation models (ParentCategory, ServiceCategory, Service, ServiceOption, PaymentMethod, PaymentDetailField, SiteConfiguration), 9 migrations (add models → seed HU translations from existing column data → drop the old single-language columns), admin translation inlines (`extra=3` HU/EN/DE, formset prefix = `related_name` = `translations`), `get_translation()` + `display_*` properties with the standard fallback chain (active → HU → first), templates/views/tests converted to `display_*`. Suite 167→170.

**Decision #39 — cross-cutting audit (commit `a0ee563`):** audited EVERY customer-visible surface (templates, views, forms, model choices, emails, JS, SEO, Category C fields). 8 gaps fixed — 7 Category A (HairLength/Status choices wrapped `gettext_lazy` + removed a `|cut` template hack, hardcoded view strings, footer tagline, footer business name via `display_business_name`, wizard group heading via `display_group_name`) and 1 Category B (`Provider.bio` + `bio_en`/`bio_de` columns added at the time). 1 known limitation documented: `admin_notes` is free-form admin text (Category C) — admin writes it in the customer's language. 18 new msgids ×3 (365 total), 2 migrations (59 total).

**Decision #40 — deep audit + ProviderTranslation (commit `6ea1605`):** deep project audit (spec vs implementation, model/template/view/admin, security, unused code). `Provider.bio` converted from the per-language-column scheme to a `ProviderTranslation` model (provider FK + language + bio, `unique_together`), eliminating the second translation pattern — 8 Translation models total, 60 migrations. All stale spec documentation corrected (EXECUTION_RULES counts/branch names, MASTER_CONTEXT, ARCHITECTURAL_PRINCIPLES header + §5 table, README). Audit verdict: no production risks, no unused code.

---

## Least-Change Ruling + Provider Bio Verification ✅ COMPLETE (Aug 21, 2026 — Decision #41, commit `4cdea1e` + follow-up)

**Decision #41 — audit findings classified under Greg's least-change rule (commit `4cdea1e`):** every deep-audit finding classified per the three-category rule — (a) docs-only → the #40 stale-doc fixes were correct, no code touched; (b) real implementation contradiction → the Provider.bio conversion (the columns were a same-day deviation from the mandated pattern, and the "no second pattern" instruction preceded the conversion) — **stands, no rollback** (rollback would be more change/risk for zero gain); (c) historical divergence → old DECISIONS entries preserved as historical truth. Also fixed the DECISIONS.md header date missed in #40's sweep.

**Provider bio verification (this cycle, follow-up commit):** Greg asked whether HU was missing since `bio_hu` couldn't be found. Verified facts:
- `bio_hu` **never existed** — the pre-#40 scheme was `bio` (HU base, no suffix) + `bio_en` + `bio_de`.
- Migration `0005_provider_translation` maps `bio` → `ProviderTranslation(language="hu")`, copying each column **only when non-empty** (no blank rows pollute the fallback chain).
- The live DB audit showed the migration preserved **100% of existing data**: only a `hu` row existed because `bio_en`/`bio_de` had been blank since their creation in `0004` (never populated). Nothing was lost.
- Fixed the dev demo data (local DB only, not tracked): provider "Amina" now has genuine HU/EN/DE bios.
- **Regression tests added** — `apps/providers/tests.py` was an empty stub; now 6 tests pinning the fallback contract: HU-only served in every language, all-three each served, missing middle language falls back to HU (not first-available), zero-rows → empty string, explicit `get_translation(lang)`, and `(provider, language)` uniqueness. Suite 170 → **176**.

**Fresh-clone verification (Aug 21):** temp-DB `migrate` from zero = all 60 migrations apply cleanly (the `0005` data copy is a safe no-op over an empty table), `makemigrations --check` clean, `manage.py check` 0 issues. Full suite 176/176. Temp DB deleted. `main` is ready for a fresh local clone and end-to-end testing.

---

## Session Management Policy (for HICLAW)

**Context windows fill up.** When working on a long project like this, sessions accumulate context. Here's the policy:

- If your context window is getting full (above ~70%), start a fresh session for the next phase.
- The specs are in the repo — re-read them in the new session.
- Don't force through a big phase on a half-full context — quality degrades.
- Starting fresh is NOT failure. It's good practice.
- Each new session should re-read: this file (PROGRESS_HISTORY.md), MASTER_CONTEXT_AND_SPECS.md, and DECISIONS.md.
