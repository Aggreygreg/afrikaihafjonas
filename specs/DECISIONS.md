# Afrikai Hajfonás — Key Decisions & Rationale

**Last Updated:** August 17, 2026

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

> **Current state (Aug 2026):** the `payments` app is fully decommissioned (commit `e2687c8`) — empty shell, out of `INSTALLED_APPS`, migrations deleted. Payment methods are admin-managed `PaymentMethod`/`PaymentDetailField` records in `apps.bookings` (Decision/Phase 7B), frozen per-appointment via `AppointmentPaymentSnapshot`.

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

**Update Aug 18, 2026:** The "exactly three ParentCategories" implication of this decision is **superseded by Decision #35** — ParentCategory is now dynamic/admin-defined. The age-validation and `target_audience` parts of this decision remain fully in force (ParentCategory stays purely navigational; age policy never moved to categories).

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

### 10. Branching: main4qp Integration Branch (LEGACY — merged Aug 17, 2026)
**Decision:** All QwenPaw development happened on `main4qp`, forked from `main`. Feature branches forked from `main4qp` and merged back into it. Final merge into `main` when stable.

**Status:** ✅ Complete — `main4qp` was merged into `main` (commit `ef16dc7`) and verified (98/98 tests, migration audit, fresh-DB migrate). **New development now branches directly from `main`.** `main4qp` is retained for history only.

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

### 18. Language Preference Modal (IMPLEMENTED — Phase 6, mechanism revised)
**Decision:** A modal appears for first-time visitors asking them to choose their preferred language (Hungarian, English, or German).

**Rationale:** The target market is Europe (Hungary-based salon with international clients). Hungarian is the default, but English and German support is essential. The modal ensures users see the site in their language from the start.

**Actual implementation (shipped):**
- Centered modal overlay (`#lang-modal-overlay` in `base.html`) with three language buttons
- No close button — user MUST pick a language
- Each button is a form POST to Django's built-in `/i18n/setlang/` view, which sets the `django_language` cookie + session language and redirects back to the same path
- **No URL language prefixes** — all languages share the same URLs; `LocaleMiddleware` resolves from cookie/session
- Shown once only: revealed by JS when the `django_language` cookie is absent
- A header dropdown language switcher is also available for later changes

> **Note:** the original design sketched a `localStorage` + `/en/`-prefix mechanism; the shipped implementation uses the `django_language` cookie + `set_language` view instead (simpler, server-visible). This is also why hreflang tags were deferred (see ARCHITECTURAL_PRINCIPLES §9.5).

**Impact:** Modal partial in `base.html`. ✅ Complete.

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

**Implementation:** ✅ Complete — Phased as Phase 7 (A-E). All tracks built, tested, and merged to `main4qp`. See `ARCHITECTURAL_PRINCIPLES.md` (Rev 3) and `PROGRESS_HISTORY.md` for full implementation details.

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
**Decision:** Admin-authored email templates use regex-based `{{ key }}` string substitution for rendering, NOT Django's `django.template` engine. This prevents template tag injection (`{% load %}`, `{% include %}`).

**Rationale:** Admin-authored content must not have access to Django's template tag system. Regex substitution limits the admin to simple `{{ placeholder }}` replacement.

**Impact:** Email rendering service uses `re.sub(r'\{\{(\w+)\}\}', ...)` instead of `django.template.Template().render()`.

---

### 35. ParentCategory Is Dynamic & Admin-Defined (ID-Based Selection)
**Date:** Aug 18, 2026 · **Branch:** `feature/dynamic-parent-categories` (not yet merged)

**Decision:** The top-level tabs on `/services/` are generated from `ParentCategory` records instead of being hardcoded to Women's/Men's/Children's. An admin-created ParentCategory automatically becomes a selectable tab. This **supersedes** the "strictly limited to exactly three entries" wording in the original model spec and the three-entry implication of Decision #4.

**Scope of the change (deliberately narrow):**
- Selection is ID-based (`?cat=<pk>`); category names are display-only, never used for matching. The old `gender` name param and the `name__icontains` lookup were removed (this was the "Men's Braids matches Women's Braids" substring bug, formerly Known Issue #2).
- Tab order = creation order (`order_by("pk")` in the view; `Meta.ordering = ["name"]` deliberately NOT used — alphabetical would reorder tabs to Children's/Men's/Women's). The classic seed order Women's → Men's → Children's preserves the original presentation; new categories append at the end. Default tab = first category in creation order (Women's with classic seeds — matches previous behavior).
- No schema change: `sort_order` and `is_active` fields were evaluated and **rejected for this iteration** (no current requirement justifies a migration; admin can already delete a category via existing CASCADE). If reordering or hiding-without-deleting becomes a real requirement, add fields then.
- Single `/services/` URL architecture unchanged; no category landing pages, no slugs, no category SEO URLs, no category images.
- Subcategory sidebar, search/price/duration/discount/sort filters, HTMX partial path, and native no-JS fallback all preserved.
- The grid's per-category accent color (pink/blue/amber) remains name-keyed for the classic trio; **any other category renders with the existing neutral gray fallback** — no color-management feature.
- Bonus fix in the same code path: tab highlight now syncs on HTMX swap (previously Known Issue #3) — tabs sit outside the swapped wrapper, so `switchCategory()` toggles the active classes client-side.

**Translation consequence (documented, NOT solved here):** Category labels are single-language DB values rendered verbatim (`{{ parent.name }}`). The previous `{% trans "Women's Braids" %}` wrappers were **inert** — those strings were never msgids in any `.po` file, so customers saw English tab labels in HU/EN/DE before this change too. Customer-visible behavior is identical; the fake translation wrappers are simply gone. If multilingual category names become a real requirement, apply the Category B pattern (parent + Translation records, per ARCHITECTURAL_PRINCIPLES) as a separately approved change. Do NOT assume category labels are translated.

**Impact:** `apps/services/views.py` (ID-based `cat` param), `templates/services/service_list.html` (dynamic tab loop, `cat` hidden input, `switchCategory()`), `apps/services/tests.py` (rewritten + expanded). No migrations, no `.po` changes. Suite 102 → 123 tests.

---

### 36. Public FAQ Page + Announcement Rendering; Docker / Health-Check / Media Cleanup; Mobile Catalog & Info-Page Fixes
**Date:** Aug 19, 2026 · **Branch:** `feature/public-faq-site-content` (off `main` @ `be80e7b`; not yet merged)

**Context:** The prior-cycle audit (Decisions/Progress through #35) left three documented gaps: the `FAQ` model existed with no public page, the `Announcement` model existed but was never rendered, and scaffold-era dead artifacts (`Dockerfile`, `docker-compose.yml`, `SECURE_REDIRECT_EXEMPT` health-check line, legacy `media/` dir, broken `ServiceImage` rows) persisted. This decision closes those gaps and fixes two mobile visual defects surfaced during the final UI/UX QA.

**36a — FAQ topics + public `/faq/` page (Category B, parent + translations):**
- New `FAQTopic` (display_order/is_active) + `FAQTopicTranslation` (topic FK/language/name, unique_together). `FAQ.topic` is a nullable FK (`on_delete=SET_NULL`) so deleting a topic keeps its FAQs.
- View `faq_page` (`site_config/views.py`): groups active FAQs under active topics (display order); ungrouped FAQs fall into a final "General" section. HU fallback per the project language rules. Search matches the question plus `strip_tags(answer)` substring (debounce 400ms, `#faq-list` outerHTML HTMX swap); native GET form fallback. Empty + no-results states. Sitemap entry added; nav placeholders (desktop/mobile/footer) → `{% url 'faq' %}`.
- Templates: `templates/pages/faq.html` (hero + search box) + `templates/pages/partials/faq_list.html` (`<details>` accordion + expand/collapse-all via event delegation). Answer bodies render `|safe` (bleach-sanitized on save, same contract as `ContentBlock`).
- Admin: `FAQTopicAdmin` (TabularInline ×3 languages) + topic added to `FAQAdmin` (list_display/list_filter).
- Migration `site_config/0012_faq_topics`.

**36b — Announcement banner rendering (existing model, newly surfaced):**
- `Announcement`/`AnnouncementTranslation` were already complete (Phase 7D); this cycle renders them. New `get_active_announcements` template tag: active + `starts_at`/`ends_at` scheduling window, `display_order`, per-language with HU fallback, skips announcements without a usable translation.
- `base.html` renders the banner stack above the sticky header; `is_dismissible` announcements get a dismiss button. Dismissal is **client-side** (localStorage keyed by slug) — no server round-trip, no per-user model. The `message` field is a plain `CharField` (intentionally **not** WYSIWYG — see admin comment), so `{{ message }}` auto-escaping is the correct safe-rendering contract (HTML/script-like content fails safe).

**36c — Multilingual admin-content architecture verified (not reinvented):**
- Confirmed `FAQ`/`FAQTopic`/`ContentBlock`/`Announcement`/`EmailTemplate`/SEO all follow the established **parent + per-language translation** pattern (Category B). No `{% trans %}` for DB-managed business content. Language fallback (active → HU base) verified live in EN and DE.

**36d — Dead artifact cleanup:**
- `Dockerfile` + `docker-compose.yml` removed (scaffold-born at `4c73354`, never developed — no CMD, no pip install; README/DEPLOYMENT have always documented the venv flow as supported). DEPLOYMENT.md had zero Docker references — no doc change needed.
- `SECURE_REDIRECT_EXEMPT = [r"^/health-check/?$"]` removed from the `if not DEBUG` block (origin: `45f558b`; no consumer — gunicorn/nginx serve directly). `SECURE_SSL_REDIRECT` retained.
- Legacy empty `media/` dir removed; 4 dev `ServiceImage` rows repointed to real tracked files in `mediafiles/`. **This is dev/demo data only** — no permanent production ownership of the current demo images is claimed; in production the administrator manages service images. Media architecture is unchanged.

**36e — Mobile visual defects (final UI/UX QA):**
- Catalog `/services/` parent-category pill bar overflowed 16px at 375px (4 pills, `w-fit`, no wrap). Fix: `max-w-full overflow-x-auto` on the bar + `whitespace-nowrap shrink-0` on pills (SHEIN-style horizontally-scrollable category bar; desktop unchanged).
- Info-page hero `<h1>` overflowed 55px at 375px on long unhyphenated DE/HU words (e.g. "Datenschutzerklärung") because `whiteSpace:normal` wraps between words but not within. Fix: `break-words` (`overflow-wrap: break-word`) on all 5 hero h1s (about/contact/faq/privacy/terms) — activates only when a word would overflow, no layout change otherwise.

**36f — Generic CMS / information-page architecture: evaluated and intentionally deferred.**
- Final information-content audit (About, Terms, Privacy, FAQ, Contact, How-It-Works, booking/payment/cancellation info, announcements) confirms the existing **smallest-appropriate-architecture** is sufficient: `ContentBlock` for long-form static prose; `FAQ`+`FAQTopic` for knowledge-style expandable content; specialized models (`PaymentMethod`, `Service`, etc.) for structured business data; `Announcement` for temporary site-wide notices.
- A generic CMS / reusable "topic page" abstraction was evaluated against the repository/specification and found **not required** by the current product. Deferred explicitly — do not introduce one without a proven spec requirement. No speculative informational pages were built.

**Test-count clarification (no historical record altered):** Decision #35's "Suite 102 → 123 tests" is **correct** (74 site_config + 25 services + 18 bookings + 6 config = 123 across the 7 test modules, with `providers`/`users`/`payments` as empty stubs). An earlier internal note misread a 3-app partial count (117) as the "real baseline" and labelled 123 an overcount — that was wrong; 117 simply omitted `config/tests.py` (6 tests). The historical 123 stands uncorrected.

**Impact:** `apps/site_config/` (models, admin, views, templatetags, tests), `config/` (settings, sitemaps, urls), 3× `.po` (+18 msgids each, compiled 341/341 ×3), `templates/base.html` + 5 info-page h1s + `service_list.html`, new `templates/pages/faq.html` + `partials/faq_list.html`, new migration `0012_faq_topics`.

---

## Decision #37 — ServiceImage admin dropdown fix + DATABASE_URL safe default (2026-08-19)

**37a — ServiceImage `linked_options` dropdowns render in admin (bug fix):**

`DynamicServiceImageForm.__init__` builds per-group `_opt_{slug}` dropdown fields when `parent_service` is provided, but three gaps prevented them from rendering in the admin change form:

1. `ServiceImageInline` had no `get_fieldsets` override. Django's default fieldset only listed `Meta.fields` (`["image", "order"]`) + readonly `image_preview`, so `_opt_*` fields never appeared in the rendered HTML.
2. Naively overriding `get_fieldsets` alone caused `FieldError`: `get_formset` derives its `fields` list from `flatten_fieldsets(get_fieldsets(...))` and passes it to `modelform_factory`, which validates field names against the model. `_opt_*` are not model fields.
3. `ServiceImageInlineFormSet._construct_form` passed `parent_service` to regular forms, but the admin's `empty_form` property (used for the JavaScript "add" form) calls `get_form_kwargs(None)` directly, bypassing `_construct_form`. The empty form had no `_opt_*` fields, causing `KeyError` during rendering.

Fix (3 changes in `apps/services/admin.py`):

1. **`get_fieldsets` override on `ServiceImageInline`**: computes `_opt_{slug}` field names from `obj.get_options_grouped()` and includes them in the fieldset for rendering. `obj` is the parent **Service** (Django passes the parent model to inline `get_fieldsets`, not the inline's own instance). Falls back to base fields when `obj` is None (add view) or has no option groups.
2. **`get_formset` override on `ServiceImageInline`**: passes `fields=list(self.form._meta.fields)` explicitly to `super().get_formset()` so `modelform_factory` sees only real model fields (`["image", "order"]`), while `get_fieldsets` still controls rendering.
3. **`get_form_kwargs` override on `ServiceImageInlineFormSet`** (replacing the old `_construct_form` override): injects `parent_service=self.instance` into the form kwargs. This is the correct hook because `get_form_kwargs` is called by BOTH `_construct_form` (regular/extra forms) AND `empty_form` (add form), so all forms receive the parent Service and build the dynamic dropdowns.

Verified: admin change form renders `<select name="images-0-_opt_color">`, `<select name="images-0-_opt_length">`, `<select name="images-__prefix__-_opt_color">`, `<select name="images-__prefix__-_opt_length">`. Both the existing form and the add form show the dropdowns with correct option labels (including `+{price} Ft` suffixes).

**37b — `.env.example` DATABASE_URL safe default (footgun fix):**

Fresh-clone audit found that `.env.example` had `DATABASE_URL=` (empty string). `dj_database_url.config()` returns `{}` when the env var is set to empty (even with a `default=` parameter, because `os.environ.get()` returns the actual empty string, not the default). Django then crashes: "improperly configured. Please supply the ENGINE value."

Fix (2 changes):

1. `.env.example`: changed `DATABASE_URL=` to `DATABASE_URL=sqlite:///db.sqlite3` (working dev default; the comments above already explained the format).
2. `config/settings.py`: replaced `dj_database_url.config(conn_max_age=600, ssl_require=False)` with `dj_database_url.parse(os.environ.get("DATABASE_URL", "").strip() or "sqlite:///db.sqlite3", conn_max_age=600, ssl_require=False)`. Uses `parse()` directly with a computed URL, handling all cases: unset env var, empty string, or a real PostgreSQL/SQLite URL.

Fresh-clone impact: `cp .env.example .env && python manage.py migrate` now works immediately without manually setting `DATABASE_URL`.

**Impact:** `apps/services/admin.py`, `config/settings.py`, `.env.example`, `apps/services/tests.py`, `specs/DECISIONS.md`. Suite 167 to **170 tests** (3 new `ServiceImageDropdownTests`: dropdown fields render, option values present, no-dropdowns for services without options). 48 applied migrations (unchanged -- no model changes).

---

## Decision #38 — Full customer-facing multilingual support (2026-08-20)

**Greg explicitly overrules Decision #35's deferral.** All customer-visible text — not just developer UI strings — must be available in HU/EN/DE.

**Scope:** Every piece of text a customer sees on the website is now backed by Translation models:
- `ParentCategoryTranslation` (name)
- `ServiceCategoryTranslation` (name)
- `ServiceTranslation` (title, description, best_for_hair_types, suitability_warning)
- `ServiceOptionTranslation` (group_name display, value)
- `PaymentMethodTranslation` (name)
- `PaymentDetailFieldTranslation` (label)
- `SiteConfigurationTranslation` (business_name, hero_title, hero_subtitle)

**Design pattern (Category B — parent + translations):**
- Each parent model retains only structural fields (ordering keys, FKs, pricing). All text fields are removed and moved to a per-language Translation model.
- Each Translation model has `unique_together = (parent_fk, language)` and uses `LanguageChoices` (HU/EN/DE).
- `get_translation(lang=None)` resolves active language with HU fallback.
- `display_*` properties (e.g., `display_name`, `display_title`) expose the resolved translation for templates and views — keeping templates skinny.
- `ServiceOption.group_name` is retained as a structural grouping key (like `FAQTopic.display_order`); the customer-visible display name lives in the translation.
- `_build_options_snapshot` stores `display_group_name`/`display_value` at booking time — correct frozen historical snapshot behavior.
- Template category matching switched from string-based (`{% if "Women" in parent.name %}`) to pk-based (`{% if parent.pk == 1 %}`) — language-agnostic.

**Migration strategy (3 phases per app):**
1. Create Translation model tables (no parent change)
2. Data migration: copy existing HU values into translations
3. Remove old text fields from parent models + update Meta

9 new migrations across 3 apps: `services` (0007-0009), `bookings` (0008-0010), `site_config` (0013-0015). Total: 48 + 9 = **57 applied migrations**.

**Admin:** TabularInline/StackedInline for each Translation model (extra=3 for HU/EN/DE). Parent admins show `display_*` in `list_display`/`search_fields`. `ServiceOptionTranslation` and `PaymentDetailFieldTranslation` registered as independent admin pages (Django does not support nested inlines). `TARGET_AUDIENCE_CHOICES` wrapped with `gettext_lazy`; `formatted_duration` uses `ngettext` for plural forms.

**i18n:** 6 new msgids added to all 3 .po files (341 to 347 entries each). Compiled via `_compile_mo.py` (polib).

**Tests:** All test helpers (`make_service`, `make_parent_category`, `make_service_category`, `make_service_option`) now create parent + Translation in one step. Admin CRUD tests use inline formset POST data (prefix = `translations`, from `related_name`). 170/170 tests pass.

**Impact:** `apps/services/{models,admin,views,tests}.py`, `apps/bookings/{models,admin,views,forms,notifications,tests}.py`, `apps/bookings/management/commands/send_expiry_reminders.py`, `apps/site_config/{models,admin,context_processors,tests}.py`, `config/tests.py`, 13 template files, 9 migration files, 3 .po files. `specs/DECISIONS.md`, `README.md`.

---

## Decision #39 — Cross-cutting customer-facing multilingual audit & fixes (2026-08-20)

**Greg required: don't assume the multilingual work (Decision #38) is complete.** A cross-cutting audit of every customer-facing surface — every URL, template, partial, view, form, model choice, email, JS string, and admin-entered free text — was performed to find remaining gaps.

**Audit method:** Read every customer-facing template, every view, every form, every model with customer-visible choices, the email notification pipeline, and the JSON-LD context processor. Classified findings into:
- **Category A** — hardcoded strings not wrapped in `gettext_lazy`/`{% trans %}` (fix: wrap + add to .po)
- **Category B** — database content not backed by a Translation model (fix: add multilingual fields)
- **Category C** — free-form admin text shown to customers (no technical fix — documented as known limitation)

**Gaps found and fixed (Category A — 7 gaps):**
1. `AppointmentRequest.HairLength` choices — were plain English strings ("Ear Length", etc.) with a `{{ label|cut:" Length" }}` template hack. Fixed: wrapped with `gettext_lazy`, changed to short-form labels ("Ear", "Chin", etc.), removed the `|cut` hack.
2. `AppointmentRequest.Status` choices — were plain English strings ("Pending Verification", etc.). Shown to customers via `get_status_display()` on the Guest Lookup badge. Fixed: wrapped with `gettext_lazy`.
3. `load_available_slots_view` — hardcoded English HTML error messages. Fixed: wrapped with `_()`.
4. `consult_wizard_view` — hardcoded `"Invalid action"` response. Fixed: wrapped with `_()`.
5. `base.html` footer tagline — "Braids that rhyme with time." was hardcoded. Fixed: wrapped with `{% trans %}`.
6. `base.html` footer copyright — hardcoded "Afrikai Hajfonás" instead of using SiteConfiguration. Fixed: uses `{{ config.display_business_name }}`.
7. `wizard_step_1.html` group heading — used `{{ group.group_name }}` (structural HU key) instead of `{{ group.display_group_name }}` (translated). Fixed.

**Gaps found and fixed (Category B — 1 gap):**
8. `Provider.bio` — customer-visible in wizard Step 2 (`{{ providers.0.bio }}`), was single-language. Provider model also had duplicate `display_name`/`bio` field declarations. Fixed: added `bio_en`/`bio_de` fields + `display_bio` property with HU fallback; removed duplicate declarations; updated admin fieldsets and template.

**Known limitation (Category C — 1 item):**
9. `AppointmentRequest.admin_notes` — free-form TextField, admin-entered, shown to customers on Guest Lookup page. Cannot be translated per-instance. Documented as accepted limitation: admin should write notes in the customer's language or in HU (base language).

**i18n:** 18 new msgids added to all 3 .po files (347 → 365 entries each). 9 HairLength labels, 5 Status labels, 3 view strings, 1 footer tagline. Compiled via `_compile_mo.py`.

**Migrations:** 2 new — `providers/0004_add_provider_multilingual_bio` + `bookings/0011_alter_hair_length_choices_multilingual`. Total: 57 + 2 = **59 applied migrations**.

**Tests:** 170/170 pass (no test changes needed — no tests directly reference choice labels or hardcoded view strings).

**Impact:** `apps/bookings/{models,views}.py`, `apps/providers/{models,admin}.py`, `templates/base.html`, `templates/bookings/partials/{wizard_step_1,wizard_step_2,wizard_step_3}.html`, 2 migration files, 3 .po files, 3 .mo files. `specs/DECISIONS.md`, `README.md`.

---

## Decision #40 — Provider.bio: convert to ProviderTranslation for architectural consistency (2026-08-20)

**Greg required:** deep audit of the entire project — verify multilingual completeness, review whether `Provider.bio`'s `bio_en`/`bio_de` scheme conforms to the established translation architecture. **"Do NOT introduce a second translation pattern unless necessary."**

**Finding:** Decision #39 added `bio`/`bio_en`/`bio_de` fields to `Provider` — a "column-per-language" pattern. This is architecturally inconsistent with `ARCHITECTURAL_PRINCIPLES.md` §4, which mandates the **parent + Translation** pattern for ALL admin-managed multilingual content. All 7 other multilingual content types use parent+Translation models (even `PaymentMethodTranslation`, which has just one field `name`). Provider.bio was the ONLY model using a second pattern.

**Decision:** **Convert** to `ProviderTranslation` model (provider FK + language + bio). This eliminates the second translation pattern and makes Provider consistent with all other Category B models.

**What changed:**
1. `Provider` model: removed `bio`/`bio_en`/`bio_de` fields; added `get_translation()` method + `display_bio` property using the standard fallback chain (active → HU → first available). Provider now has structural fields only (`display_name`, `user`, `profile_image`).
2. New `ProviderTranslation` model: `provider` FK (related_name=`translations`), `language` (LanguageChoices), `bio` (TextField). `unique_together = (provider, language)`.
3. `ProviderAdmin`: added `ProviderTranslationInline` (StackedInline, extra=3 for HU/EN/DE); updated fieldsets to remove bio fields.
4. Migration `0005_provider_translation`: CreateModel(ProviderTranslation) → RunPython (copy bio→HU, bio_en→EN, bio_de→DE) → RemoveField(bio, bio_en, bio_de). Data migration preserves existing bio content.
5. Template `wizard_step_2.html`: already used `{{ providers.0.display_bio }}` — no change needed.

**Deep audit — additional findings (all documentation staleness, all fixed):**
- `EXECUTION_RULES.md`: Rule 9 (i18n) updated from "341 msgids, wrap now/translate later" to "365 msgids, FULLY BUILT with catalog Translation models". Known Gotcha #2 corrected (labels ARE translated, not single-language). Migration count 48→60. Test count 167→170. Builder Agent Context + Worktree sections: `main4qp` → `main`.
- `MASTER_CONTEXT_AND_SPECS.md`: §2 translations 341→365. §3 ParentCategory "single-language" → "fully translated". §3 migration count 47→60. §3 Provider description updated to mention ProviderTranslation.
- `ARCHITECTURAL_PRINCIPLES.md`: header updated (Aug 20, Rev 6, 170 tests). §5 SiteConfiguration table corrected: business_name/hero_title/hero_subtitle now shown as SiteConfigurationTranslation (Category B), not single-language or `{% trans %}`.
- `README.md`: showmigrations 48→60. i18n strings 341→365. Decision range #1–#35→#1–#40. Migration count note 59→60.

**Migrations:** 1 new — `providers/0005_provider_translation`. Total: 59 + 1 = **60 applied migrations**.

**Tests:** 170/170 pass. `makemigrations --check`: clean. `django check`: 0 issues.

**Impact:** `apps/providers/{models,admin}.py`, `apps/providers/migrations/0005_provider_translation.py`, `specs/{ARCHITECTURAL_PRINCIPLES,DECISIONS,EXECUTION_RULES,MASTER_CONTEXT_AND_SPECS}.md`, `README.md`.
