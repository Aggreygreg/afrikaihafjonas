# Afrikai Hajfonás — Key Decisions & Rationale

**Last Updated:** August 12, 2026

---

## Decision Log

### 1. Appointment Request & Hold System (NOT Instant Booking)
**Decision:** Clients cannot instantly book slots. They submit a consultation request with hair photos and a deposit, which places a 12-hour hold. Admin manually approves or rejects.

**Rationale:** African hair braiding requires specific hair lengths, thicknesses, and age requirements. Instant bookings would lead to unsuitable appointments, wasted stylist time, and awkward cancellations. Manual review protects both the salon and the client.

**Impact:** Entire `bookings` app rewritten. State machine introduced. Admin dashboard required.

---

### 2. Manual Bank Transfers Only (No Payment Gateways)
**Decision:** Removed Stripe, PayPal, Barion. All payments are manual bank transfers (Revolut, Wise, TransferGo, Bank Transfer) with screenshot proof upload.

**Rationale:** Third-party gateways charge fees. For a salon business with high-value transactions (up to 90,000 Ft), even 2-3% fees are significant. Manual transfers eliminate processing costs.

**Impact:** `payments` app obsolete. RefundQueue proxy model needed for manual refund tracking. Admin must manually verify payments and process refunds.

---

### 3. No Customer Reviews
**Decision:** The `apps.reviews` module was intentionally deleted. No star ratings, no comments, no review system.

**Rationale:** Keep the platform lightweight and focused. Reviews add moderation burden, potential for abuse, and complexity without proportional value for a salon booking system.

**Impact:** Reduced codebase complexity. No review-related models, views, or templates.

---

### 4. Children's Braids Category
**Decision:** Added `Children's Braids` as a third `ParentCategory` alongside Women's and Men's Braids.

**Rationale:** Children's braiding is a distinct service category with different suitability requirements (age 8-15), pricing, and safety considerations. It needs its own filtering and visibility in the catalog.

**Impact:** `ParentCategory` model updated. `target_audience` field added to `Service`. Age validation logic required.

---

### 5. Age & Suitability Gates
**Decision:** Services have `target_audience` (Adults 16+, Children 8-15, Everyone 8+), `best_for_hair_types`, and `suitability_warning` fields. Frontend enforces age validation during consultation.

**Rationale:** Some hairstyles are physically inappropriate for children or require specific hair types. Preventing mismatched bookings protects clients from disappointment and the salon from liability.

**Impact:** `Service` model extended. Consultation Wizard Step 3 includes age gate. Frontend validation blocks submission with friendly error.

---

### 6. SHEIN-Style E-Commerce Detail Page
**Decision:** Service detail page follows e-commerce product page conventions: dynamic image gallery, option selection (radio cards ≤4, dropdown >4), style details above suitability info.

**Rationale:** Clients browsing hairstyles are making visual, aesthetic decisions. A premium, familiar e-commerce experience (like SHEIN) reduces friction and increases conversion. The option-based image switching lets clients see exactly what their configured style looks like.

**Impact:** `ServiceImage` model upgraded with M2M `linked_options`. Custom admin formset for dynamic option dropdowns. Vanilla JS for image matching logic.

---

### 7. Fat Models, Skinny Templates
**Decision:** All business logic (time formatting, deposit calculations, duration strings) lives in Django model `@property` methods or `utils.py`, never in template tags or view logic.

**Rationale:** Keeps templates clean and readable. Makes logic testable. Prevents duplication across templates. Follows Django best practices.

**Impact:** `Service.formatted_duration` property. Deposit calculation in `utils.py`. Time slot calculation in `utils.py`.

---

### 8. HTMX Multi-Step Wizard (Not Massive Scrolling Form)
**Decision:** The consultation process is a 4-step HTMX wizard with card-based steps, not a single long form.

**Rationale:** A 4-step process with photos, deposits, and age validation would be overwhelming as a single form. Step-by-step reduces cognitive load, allows progressive validation, and feels more premium.

**Impact:** 4 distinct HTMX partials. Each step validates before allowing progression. `hx-target` IDs must match precisely.

---

### 9. 12-Hour Hold Timer
**Decision:** When a client submits a consultation request, the time slot is held for exactly 12 hours. If no admin action, the request auto-expires and the slot is freed.

**Rationale:** Prevents slots from being indefinitely locked by unreviewed requests. 12 hours gives admins a reasonable window to review during business hours while ensuring slots don't stay blocked for days.

**Impact:** `held_until` field on `AppointmentRequest`. Background task or admin dashboard check for expired requests. Auto-expiry logic.

---

### 10. Branching: main4qp Integration Branch
**Decision:** All QwenPaw development happens on `main4qp`, forked from `main`. Feature branches fork from `main4qp` and merge back into it. Final merge into `main` when stable.

**Rationale:** Protects the production `main` branch from experimental AI-generated code. Provides a stable integration branch for testing before production deployment.

**Impact:** Git workflow established. All commits target `main4qp`.

---

### 11. Proxy Model for Refund Queue
**Decision:** `RefundQueue` is a Django proxy model pointing to `AppointmentRequest`, filtered to `rejected` and `expired` statuses.

**Rationale:** Refunds are manual bank transfers — there's no API to call. The admin needs a dedicated view to see who needs money sent back, without mixing with active requests. A proxy model is the cleanest Django pattern for this.

**Impact:** `RefundQueue` model in `bookings` app. Custom `get_queryset` override. Admin registration.

---

### 12. Dynamic M2M Image-Option Linking
**Decision:** `ServiceImage` uses a `ManyToManyField` to `ServiceOption` (not FK, not JSON). Images can represent combinations of options (e.g., "Black" + "Waist Length").

**Rationale:** Hairstyle images depend on multiple option dimensions (color, length, density). A single FK wouldn't capture combinations. M2M allows one image to match multiple option selections, and the frontend JS calculates the "best match" score.

**Impact:** `linked_options` M2M field. `linked_options_json` property for frontend. Custom admin formset with dynamic dropdowns per option group.

---

### 13. Wizard Step Mapping (Spec vs Built)
**Decision:** Keep our 4-step wizard structure (Configure → Schedule → Details → Review) rather than restructuring to match the master spec's 4 steps (Stylist+Date → Client Details → Hair Data → Finances).

**Rationale:** Phase 3 already built and verified Steps 1-2 (options config + scheduling). The master spec doesn't include "options config" as a wizard step — it happens on the detail page. Our wizard adds an extra options step which is better UX (SHEIN-style configuration before scheduling). The content of each step matters more than the numbering.

**Mapping:**
- Our Step 1 (Configure) = Options config — NOT in master spec's wizard
- Our Step 2 (Schedule) = Master spec Step 1 (Stylist + Date)
- Our Step 3 (Details) = Master spec Steps 2+3 combined (Client Details + Hair Data)
- Our Step 4 (Review) = Master spec Step 4 (Finances)

**Impact:** Progress bar stays at 4 steps. Steps 3-4 content is mapped from the master spec but combined differently.

---

### 14. Draft Approach for AppointmentRequest Creation
**Decision:** Create the `AppointmentRequest` at Step 3 submit (with client data + hair photos), then update it at Step 4 with payment method + proof of payment.

**Rationale:** The fundamental challenge is multi-step HTMX wizards with file uploads. Files can't persist across HTMX step transitions without temp storage. The draft approach avoids temp storage entirely by creating the record early.

**Implementation:**
- Step 3 submit: Creates AppointmentRequest with `status=pending_verification`, all text data + hair photos. `proof_of_payment` left blank (requires `blank=True` on model).
- Step 4: Shows the record's deposit + reference. User uploads proof + selects payment method. Submit updates the record.
- Confirmation page: Shows reference code + next steps.

**Impact:** Requires one model change: `proof_of_payment = models.ImageField(blank=True, ...)`. Safe because no AppointmentRequest objects exist yet.

---

### 15. Guest Lookup Show/Hide Rules
**Decision:** Client-facing Guest Lookup page shows admin notes but hides proof of payment images and internal notes.

**What to SHOW:**
- Status (with colored badge)
- Requested date/time
- Admin notes (labeled "Admin note: ...")
- Deposit amount
- Payment method
- Payment reference (AFH-XXXXXX)
- Payment status
- Brief explanation of what each status means

**What to HIDE:**
- Proof of payment image (bank screenshot — sensitive account/transaction info)
- Internal payment notes
- Bank transfer details from admin side

**Rationale:** Showing admin notes reduces "why was I rejected?" calls. Admin learns to write professionally knowing notes are client-visible. No internal-only toggle needed — this is hair appointments, not medical records.

**Impact:** Guest Lookup view filters `AppointmentRequest` fields for client visibility.

---

### 16. Branch Cleanup
**Decision:** Delete merged feature branches after each phase is verified.

**Rationale:** Prevents stale branches from cluttering the repo. All feature branches for Phases 2, 2.5, and 3 are fully merged into `main4qp` and safe to delete.

**Impact:** Git workflow: merge to main4qp → verify → delete feature branch.

---

### 17. Parallel Dispatch for Phase 4
**Decision:** Dispatch wizard Steps 3-4 to hack_3 and Guest Lookup to hack_1 simultaneously.

**Rationale:** Guest Lookup is independent — it's a new view + template that reads AppointmentRequest. It doesn't depend on wizard implementation. Running in parallel saves time.

**Impact:** Two feature branches created simultaneously: `feature/wizard-steps-3-4` and `feature/guest-lookup`. Merge wizard first, then guest lookup (resolving any views.py conflicts).

---

### 18. Language Preference Popup
**Decision:** A modal popup appears for first-time visitors asking them to choose their preferred language (Hungarian, English, or German). Detected via `localStorage` key `afrikai_lang_selected`.

**Rationale:** The target market is Europe (Hungary-based salon with international clients). Hungarian is the default, but English and German support is essential. The popup ensures users see the site in their language from the start.

**Implementation:**
- Centered modal overlay with three clickable cards (🇭🇺 Magyar, 🇬🇧 English, 🇩🇪 Deutsch)
- No close button — user MUST pick a language
- On selection: set `localStorage` + cookie, reload with language prefix (`/en/`, `/de/`, or default `/hu/`)
- Shown once only (localStorage check is instant, no flash)

**Impact:** Template partial in `base.html`. Django i18n middleware handles language switching. Deferred to Final Polish phase.

---

### 19. No Client Accounts
**Decision:** No user registration, login, or password management. Clients are anonymous consultation submitters with plain text fields (`client_name`, `client_email`, `client_phone`).

**Rationale:** Zero-friction checkout. Clients shouldn't need to create an account just to book a hairstyle. Admin filters `AppointmentRequest` table by email for customer history.

**Impact:** No `AUTH_USER_MODEL` FK on AppointmentRequest. No registration views. No password reset flow.

---

### 20. Background Tasks: Management Command + Cron (NOT Celery)
**Decision:** Use Django management commands + cron jobs for background tasks (expiry reminders, auto-expiry). NOT Celery.

**Rationale:** Celery is massive overkill for a single salon. A simple management command run via cron every 30 minutes handles expiry checks and email reminders.

**Impact:** `management/commands/check_expired_requests.py` or similar. Cron schedule on production server. Console email backend during development.

---

### 21. SQLite for Local Development
**Decision:** SQLite for local development, PostgreSQL for production.

**Rationale:** Fast iteration, no Docker/Postgres overhead for builders. Agents can run `makemigrations` and `migrate` instantly.

**Impact:** `.env` contains `DATABASE_URL=sqlite:///db.sqlite3`. Production uses PostgreSQL.

---

### 22. Console Email Backend for Development
**Decision:** `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` during development.

**Rationale:** Emails print to console instead of actually sending. Allows testing email notifications without SMTP setup.

**Impact:** Configured in `.env` / `settings.py`. Production uses real SMTP.

---

### 23. Session Management for Long Projects
**Decision:** When context windows fill up (above ~70%), start a fresh session. Re-read specs from repo in new session.

**Rationale:** Quality degrades on half-full contexts. Starting fresh is good practice, not failure. Specs are persistent in the repo — they survive session resets.

**Impact:** Each new session should re-read: PROGRESS_HISTORY.md, MASTER_CONTEXT_AND_SPECS.md, and DECISIONS.md.

---

### 24. Business-Managed Content & Configuration (Architectural Principle)
**Decision:** Business-owned content and configuration must be moved from hardcoded code/templates into Django Admin. Developers control system structure, logic, validation, and supported data types. Administrators control business information, email content, payment methods, payment details, SEO metadata, and customer-facing content.

**Rationale:** A routine business change (new phone number, new bank account, updated email wording, new payment service, changed SEO metadata) should never require a developer to modify code or redeploy. The salon owner needs to operate independently once the system is live.

**Scope (see ARCHITECTURAL_PRINCIPLES.md Rev 2 for full detail):**
1. Business Information — extend `SiteConfiguration` with all fields (Phase 7A)
2. Admin-Managed Payment Methods + Historical Snapshots — `PaymentMethod`, `PaymentDetailField`, `AppointmentPaymentSnapshot` (Phase 7B)
3. Editable Email Templates (multilingual) — `EmailTemplate` + `EmailTemplateTranslation` (Phase 7C)
4. Customer-Facing Content (multilingual) — FAQ, content blocks, announcements (Phase 7D)
5. SEO Configuration (multilingual) — `GlobalSEO`, `PageSEO` with translations, including per-Service SEO (Phase 7E)

**Implementation:** Phased as Phase 7 (A-E). Not started yet. All queued in ARCHITECTURAL_PRINCIPLES.md (Rev 2).

**Preserved:** All existing business rules (deposit math, 12-hour hold, age validation, photo rules, anti-patterns) remain unchanged. This principle moves **where** config lives, not **what** the rules are.

**Impact:** This is the most significant architectural evolution since Phase 0. It touches every app, every template, and the data layer. Each sub-phase must be carefully planned with data migrations and backward compatibility.

### 25. i18n Without GNU gettext (polib-based workflow)
**Decision:** Use Python `polib` package for .po/.mo file management instead of Django's `makemessages`/`compilemessages` (which require GNU gettext tools not available on this Windows machine).

**Rationale:** GNU gettext could not be installed (no admin access for choco). `polib` provides full .po read/write and .mo compilation from Python. Custom scripts (`_build_po.py`, `_apply_translations.py`, `_compile_mo.py`) replicate the gettext workflow.

**Impact:** Translation workflow is Python-based. JSON files serve as the translation source of truth; scripts apply them to .po files. .mo files are gitignored (build artifacts). After a fresh clone, run `_build_po.py` → `_apply_translations.py` → `_compile_mo.py` to regenerate catalogs.

---

### 26. Three Content Categories (Architectural Foundation for Multilingual Content)
**Decision:** All content in the system falls into exactly one of three categories, each with a distinct translation strategy:

- **Category A — Developer-Authored UI:** Static template/Python strings → Django i18n `{% trans %}` / `.po` files.
- **Category B — Admin-Authored Reusable Content:** FAQs, static page text, announcements, email templates, SEO metadata → language-specific DB records (parent + translations), NOT `{% trans %}`.
- **Category C — Appointment-Specific Free-Form Content:** `admin_notes`, `internal_notes` → no translation system. Admin writes in the customer's language, guided by the appointment's stored `customer_language`.

**Rationale:** `{% trans %}` is for developer-authored strings only. Database-managed content cannot be inserted into `.po` files at runtime. The three-category distinction prevents architectural confusion about what gets translated how.

**Impact:** Every multilingual content model in Phase 7 uses the parent + translation record pattern. `admin_notes` stays simple — just show the language indicator.

### 27. Historical Payment Snapshot (Mandatory)
**Decision:** Every appointment must have a frozen `AppointmentPaymentSnapshot` that preserves the payment method name, slug, and all detail field values as they existed at submission time.

**Rationale:** Admin may change IBANs, disable methods, or replace payment services later. Historical appointments must continue to represent the payment configuration that was valid when the customer submitted their request. Without snapshots, changing Wise's IBAN would retroactively alter what August customers were told to pay into.

**Impact:** `AppointmentRequest` keeps a FK to live `PaymentMethod` (for admin filtering), but the **authoritative payment details** shown in Guest Lookup come from the snapshot, never from live tables. See ARCHITECTURAL_PRINCIPLES.md §6.2.

### 28. Appointment Language Persistence (customer_language)
**Decision:** Every `AppointmentRequest` stores `customer_language` (hu/en/de) as a permanent field captured at submission. This field is immutable after creation and drives all transactional email language selection.

**Rationale:** An appointment's communication language must not change if the customer later switches website languages. Transactional emails use this stored value, not the session/browser language at send time.

**Impact:** The email rendering system (Phase 7C) reads `appointment.customer_language` to select the correct `EmailTemplateTranslation`. Django Admin displays the language prominently (🇭🇺 HU / 🇬🇧 EN / 🇩🇪 DE) to guide the admin when writing notes.

### 29. Transactional Emails vs Newsletters (Separate Systems)
**Decision:** Transactional email templates (`EmailTemplate`) and marketing/newsletter content are strictly separate systems. Newsletters are NOT just another `email_type` in the transactional enum.

**Rationale:** Different triggers (app event vs manual admin action), different audiences (one customer vs filtered group), different models and workflows. Collapsing them would create confusing architecture.

**Impact:** Newsletter system is explicitly out of scope for Phase 7. If needed later, it gets its own `Newsletter` model and workflow.

### 30. Corrected Payment Anti-Pattern Wording
**Decision:** The master spec anti-pattern §7.1 wording is corrected from "All payments are Manual Bank Transfers" to: "No automated third-party payment gateway integrations. Payments are manually verified using administrator-configured payment methods and instructions."

**Rationale:** The salon accepts multiple methods (Revolut, Wise, TransferGo, Bank Transfer), not just bank transfers. The method set is admin-configurable. The prohibition is on automated gateway integrations (Stripe, PayPal, etc.), not on having multiple payment methods.

**Impact:** Anti-pattern wording updated in MASTER_CONTEXT_AND_SPECS.md §7.1 and apps.payments decommission note.

---

### 31. Payment Snapshot is Admin-Only Audit — NOT Guest Lookup Data
**Decision:** `AppointmentPaymentSnapshot.detail_fields_snapshot` (IBAN, account holder, QR codes) is an admin-only audit record. It is NEVER shown to customers. Guest Lookup reads ONLY `payment_method_name` from the snapshot (to survive later method deletion). This corrects a specification error in ARCHITECTURAL_PRINCIPLES.md Rev 2.

**Rationale:** Decision #15 explicitly states "Bank transfer details from admin side — Always Hidden from Clients." The snapshot's purpose is to preserve what payment configuration existed at submission time for admin verification and dispute resolution — not to re-display payment instructions to customers. Customers see payment instructions ONLY at Step 4 (from live data), then the method name + deposit + reference in Guest Lookup.

**Impact:** ARCHITECTURAL_PRINCIPLES.md §6.2 updated. Guest Lookup view reads `snapshot.payment_method_name` only. Snapshot inline in Django Admin is read-only.

### 32. Historical Image Preservation in Payment Snapshots
**Decision:** Image-type `PaymentDetailField` values are physically copied to `payment_snapshots/<reference>/` at snapshot creation time via Django's storage API. The new immutable path is stored in the snapshot JSON.

**Rationale:** Storing just the media path is fragile — admin file replacement/deletion or storage migration would break the audit record. Copying guarantees immutability. Storage overhead is negligible (~50KB per appointment at salon volume).

**Impact:** Snapshot creation logic includes a file-copy step for image-type fields. Text values stored directly in JSON (no file dependency).

### 33. WYSIWYG for Website Content, Plain Text for Emails
**Decision:** Limited WYSIWYG editor (`django-summernote` with restricted toolbar) for website content (FAQ, ContentBlock, Announcement). Bleach sanitization on save with strict tag whitelist. Email templates use plain textarea (`body_text`) — NO WYSIWYG. Optional `body_html` is plain HTML textarea only.

**Rationale:** Salon owner is not a developer — Markdown syntax is a learning barrier. WYSIWYG with limited toolbar + bleach is intuitive and secure. Email HTML is too fragile for WYSIWYG (email clients render inconsistently, inline styles required). Different content types need different editing mechanisms.

**Impact:** `django-summernote` + `bleach` added to requirements. `@tailwindcss/typography` added to Tailwind config for rendering WYSIWYG output in `prose` containers.

### 34. Email Placeholder Security — Regex Substitution Only
**Decision:** Admin-authored email templates use regex-based `{{ key }}` string substitution for rendering, NOT Django's `django.template.Template` engine. This prevents template tag injection (`{% load %}`, `{% include %}`).

**Rationale:** Admin-authored content must not have access to Django's template tag system. Regex substitution limits the admin to simple `{{ placeholder }}` replacement.

**Impact:** Email rendering service uses `re.sub(r'\{\{(\w+)\}\}', ...)` instead of `django.template.Template().render()`.
