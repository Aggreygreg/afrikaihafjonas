# Afrikai Hajfonás — African Braiding Salon Booking Platform

A customer-facing appointment **request** platform for an African hair braiding salon in Budapest, Hungary. Built with Django 4.2, HTMX, and Tailwind CSS. Trilingual: Hungarian (base), English, German.

**This is NOT an instant-booking system.** African braiding has strict hair-length, age, and thickness requirements, so customers submit an *appointment request*: they configure a style, upload hair photos, and wire a deposit. The salon owner reviews each request in a customized Django Admin and approves or rejects it. Requested slots are held for **12 hours** before auto-expiring.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture](#architecture)
3. [Customer Journey](#customer-journey)
4. [Admin Workflow](#admin-workflow)
5. [Payments: Dynamic Methods & Historical Snapshots](#payments-dynamic-methods--historical-snapshots)
6. [Email System (8 Triggers)](#email-system-8-triggers)
7. [Multilingual Support](#multilingual-support)
8. [Admin-Managed Content](#admin-managed-content)
9. [SEO System](#seo-system)
10. [Development Setup](#development-setup)
11. [Environment Configuration](#environment-configuration)
12. [Testing & Verification](#testing--verification)
13. [Management Commands & Cron](#management-commands--cron)
14. [Production Deployment](#production-deployment)
15. [Branch Strategy](#branch-strategy)
16. [Implemented vs. Deferred](#implemented-vs-deferred)
17. [Project Documentation](#project-documentation)

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Framework | Django 4.2 (LTS) | Modular `apps/` layout |
| Interactivity | HTMX 1.9 | Loaded from CDN on wizard + catalog templates (per-template, not in base) |
| Styling | Tailwind CSS | **Loaded via CDN in `base.html`** (no npm build needed to run). A `theme/` app with django-tailwind exists for optional production builds. |
| Database | SQLite (dev) / PostgreSQL (prod) | Configured via `DATABASE_URL` |
| Server | Django `runserver` (dev) / gunicorn + nginx (prod) | |
| Admin content editing | django-summernote (limited toolbar) + bleach sanitization | Website content only — never email templates |
| Site configuration | django-solo | `SiteConfiguration` singleton |
| i18n tooling | polib (custom scripts) | No GNU gettext required |
| Testing | pytest + pytest-django | 170 tests (incl. `config/tests.py`) |

Key dependencies are managed with pip-tools: edit `requirements.in`, then recompile with `pip-compile requirements.in --output-file=requirements.txt`. Never edit `requirements.txt` by hand.

## Architecture

```
apps/
├── site_config/   # Business info singleton, FAQ/ContentBlock/Announcement,
│                  # EmailTemplate system, SEO models, context processors
├── users/         # Custom user model (admin access only — no client accounts)
├── providers/     # Stylists + weekly availability + slot overrides
├── services/      # Catalog: ParentCategory → ServiceCategory → Service,
│                  # ServiceOption add-ons, ServiceImage M2M option linking
├── bookings/      # AppointmentRequest (the operational hub), 4-step wizard,
│                  # PaymentMethod/PaymentDetailField/AppointmentPaymentSnapshot,
│                  # notifications, RefundQueue proxy, expire/remind commands
├── payments/      # DECOMMISSIONED (empty shell, kept to avoid import errors;
│                  # not in INSTALLED_APPS, migrations intentionally deleted)
└── reviews/       # DELETED (intentionally scrapped)
```

Core tenets (enforced across the codebase):

- **Fat models, skinny templates** — no math or formatting in templates; business logic lives in model properties and `utils.py`.
- **No client accounts** — clients are anonymous submitters (`client_name`, `client_email`, `client_phone`).
- **No payment gateways** — payments are manually verified transfers (see below).
- **No Celery** — background work is Django management commands + cron.
- **Currency** — Hungarian Forint, zero decimals (`8,000 Ft`).

## Customer Journey

1. **Home (`/`)** — hero (content from `SiteConfiguration`), popular services, language modal for first-time visitors.
2. **Catalog (`/services/`)** — browse by parent category tabs (dynamic, admin-defined — every `ParentCategory` record renders as a tab in creation order; the seeded trio is Women's / Men's / Children's Braids and admin-created categories appear automatically), keyword search, price range, subcategory filters. Tab selection is ID-based (`?cat=<pk>`). Live HTMX filtering (category tabs, debounced search); native "Apply Filters" form submit works without JS. *(Note: category labels are single-language DB values — see [Decision #35](specs/DECISIONS.md).)*
3. **Service detail (`/services/<id>/`)** — SHEIN-style product page: dynamic image gallery that switches with selected options, suitability info, option cards (radio ≤4 options, dropdown >4).
4. **Consultation wizard (`/bookings/book/<service_pk>/`)** — 4 steps:
   - **Step 1 — Configure:** service options (radio cards / dropdowns / add-on checkboxes), live price total.
   - **Step 2 — Schedule:** provider → date → time slot (HTMX; 30-minute grid, duration-aware, blocked-slot detection).
   - **Step 3 — Details:** client info, age validation (client + server side), hair length, 3 hair photos, GDPR consent. Creates the `AppointmentRequest` (`status=pending_verification`) and sends the `request_received` email.
   - **Step 4 — Review:** deposit amount, `AFH-XXXXXX` reference, payment method cards with live transfer details via HTMX, proof-of-payment upload, final consent. Sets the 12-hour hold, creates the payment snapshot, sends `verification_pending`.
5. **Confirmation (`/bookings/confirmation/<reference>/`)** — copyable reference + next steps.
6. **Guest Lookup (`/bookings/status/`)** — email + reference code → status, no account needed. Shows admin notes; **never** shows bank transfer details or proof-of-payment images (Decision #15/#31).

Deposit math (in `apps/bookings/utils.py`): `base_price >= 45,000 Ft → 20,000 Ft` deposit, otherwise `10,000 Ft`.

## Admin Workflow

The Django Admin at `/admin/` is the salon owner's daily operating system:

- **Custom dashboard** (`config/admin_dashboard.py` + `templates/admin/index.html`): pending verifications, pending reviews, expiring-soon holds, today's schedule, refund queue, approved deposit revenue, quick actions.
- **Appointment review flow:** verify payment (`verify_payments` action → `pending_review`) → review photos → approve (`approved`) or reject (`rejected` → Refund Queue).
- **Refund Queue:** proxy model of `AppointmentRequest` filtered to `rejected`/`expired`. Refunds are manual bank transfers; `complete_refunds` sends the refund email and does **not** change status (by design).
- **Auto-expiry:** `expire_holds` command flips past-due holds to `expired` (cron every 15 min).
- **Seasonal discounts:** inline `discount_percentage` editing + bulk actions in the Services admin.
- **Language awareness:** each appointment shows the customer's language flag (🇭🇺/🇬🇧/🇩🇪) so the owner writes `admin_notes` in the right language.

## Payments: Dynamic Methods & Historical Snapshots

There are **no payment gateway integrations** (no Stripe/PayPal/Barion — hard rule). Instead:

- **`PaymentMethod` + `PaymentDetailField`** (admin-managed, in `apps/bookings`): the owner defines which methods exist (seeded with Revolut, Wise, TransferGo, Bank Transfer) and their transfer details (IBAN, account holder, QR code image, …). Adding or changing a method requires no code.
- **`AppointmentPaymentSnapshot`**: at Step 4 submission the full payment configuration is **frozen** onto the appointment (name, slug, all detail fields as JSON; image files physically copied to immutable paths). Later edits to payment methods never rewrite history.
- **Visibility rules:** transfer details are shown to the customer **only on the Step 4 page** (live data). Guest Lookup shows only the frozen method *name*. The snapshot's detail fields are an admin-only audit record.
- `AppointmentRequest.payment_method_fk` (`SET_NULL`) links to the live method for admin filtering; the snapshot is the authoritative historical record.

## Email System (8 Triggers)

All 8 transactional emails are **implemented and verified end-to-end** (SMTP-tested). Content is admin-editable via `EmailTemplate` + `EmailTemplateTranslation` (HU/EN/DE, seeded ×3 = 24 records). Placeholders use safe regex `{{ key }}` substitution — never the Django template engine (no tag injection).

| Trigger | Email type | Fired from |
|---|---|---|
| Request submitted (Step 3) | `request_received` | `wizard_step_3` view |
| Hold placed (Step 4) | `verification_pending` | `wizard_step_4` view |
| Payment verified | `payment_verified` | `verify_payments` admin action |
| Appointment approved | `appointment_approved` | `approve_requests` admin action |
| Appointment rejected | `appointment_rejected` | `reject_requests` admin action |
| Hold expired | `appointment_expired` | `expire_holds` command |
| Refund processed | `refund_notification` | `complete_refunds` admin action |
| Expiry reminders (2h / 1h before) | `expiry_reminder` | `send_expiry_reminders` command |

Language selection uses the appointment's stored `customer_language` (captured at Step 3, immutable) — never the admin's or recipient's current browser language. Newsletters/marketing email are a deliberately separate, unbuilt system.

## Multilingual Support

- **Languages:** `hu` (Hungarian — base/default), `en`, `de`. msgids are English; translations live in `locale/*/LC_MESSAGES/django.po`.
- **Mechanism:** cookie/session-based via Django's `LocaleMiddleware` and `set_language` view (`/i18n/setlang/`). There are **no URL language prefixes** (`/en/…`); all languages share the same URLs.
- **First-visit modal:** `base.html` renders a language modal shown when the `django_language` cookie is absent; each choice POSTs to `set_language`. A header dropdown switcher is also available.
- **Two translation systems by design** (see `specs/ARCHITECTURAL_PRINCIPLES.md` §3):
  - *Developer UI strings* → `{% trans %}` + `.po` files (Category A).
  - *Admin-authored content* (FAQ, page prose, emails, SEO) → parent + per-language DB records (Category B); never `{% trans %}`.
- **polib workflow (no GNU gettext needed):** `.mo` files are gitignored build artifacts. After cloning or after editing translations run:
  ```
  python _build_po.py            # rebuild .po from source strings
  python _apply_translations.py  # apply HU/DE translations from locale/*.json
  python _compile_mo.py          # compile .po → .mo via polib
  ```
  (On a server with GNU gettext, `django-admin compilemessages` also works.)

## Admin-Managed Content

Everything the business routinely changes is editable in Django Admin — no redeploy needed:

| Content | Model(s) | Notes |
|---|---|---|
| Business info (name, address, phone, hours, socials, logo, hero, maps link) | `SiteConfiguration` (solo) | Injected site-wide via context processor |
| Static page prose | `ContentBlock` + translations | Slugs: `about_page`, `terms_page`, `privacy_page`, `about_mission`; templates fall back to hardcoded copy if a block is missing |
| FAQs | `FAQ` + `FAQTopic` + translations | Public `/faq/` page (Aug 19, 2026): admin-managed topics + Q&A, trilingual with HU fallback, HTMX search, accordion; topics group FAQs (ungrouped → "General" section). |
| Announcements/banners | `Announcement` + translations | Model + admin complete; rendered site-wide as a dismissible banner stack (Aug 19, 2026) — active + scheduling window, per-language with HU fallback, dismissed client-side via localStorage. |
| Payment methods & details | `PaymentMethod`, `PaymentDetailField` | See above |
| Email templates | `EmailTemplate` + translations | 8 types × 3 languages seeded |
| SEO metadata | `GlobalSEO`, `PageSEO` + translations | See below |

Static pages: **About** (`/about/`), **Contact** (`/contact/` — informational, data from `SiteConfiguration`), **Terms & Conditions** (`/terms/` — includes deposit/hold and refund policy sections), **Privacy** (`/privacy/`), **FAQ** (`/faq/` — admin-managed topics + Q&A). Website prose uses django-summernote with a restricted toolbar, sanitized by bleach on save; email templates stay plain text (no WYSIWYG — email HTML is too fragile).

## SEO System

- **Admin-editable metadata:** `GlobalSEO` singleton (per-language defaults) + `PageSEO` (per-URL or per-Service overrides; exactly one target enforced by DB constraint). Six static-page entries are seeded: `/`, `/services/`, `/about/`, `/contact/`, `/terms/`, `/privacy/`. Per-Service `PageSEO` is supported by the model and admin but not seeded.
- **Fallback chain:** page override → global default → hardcoded developer fallback.
- **Developer-managed (in code):** `sitemap.xml` (Django sitemaps, sectioned), `robots.txt`, JSON-LD LocalBusiness structured data, canonical logic.
- **hreflang: intentionally deferred** — meaningless without per-language URLs (see above); would require moving to `i18n_patterns`.

## Development Setup

Requires Python 3.12+ (Node.js is **not** required — Tailwind and HTMX load from CDN).

```bash
git clone https://github.com/Aggreygreg/afrikaihafjonas.git
cd afrikaihafjonas
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt

cp .env.example .env              # then edit (see below)
python manage.py migrate          # includes seed data (payment methods, email templates, SEO)
python _build_po.py && python _apply_translations.py && python _compile_mo.py   # translations
python manage.py createsuperuser
python manage.py runserver
```

- Site: http://127.0.0.1:8000 · Admin: http://127.0.0.1:8000/admin/
- Dev database: SQLite at `db.sqlite3` (gitignored).
- Emails print to the console in dev (`console` email backend).
- Uploads land in `mediafiles/` (flat paths: `hair_photos/`, `payment_proofs/`, `payment_snapshots/<ref>/`); served by Django only when `DEBUG=True`.
- ~~Docker~~ — the scaffold-era `Dockerfile` and `docker-compose.yml` were removed (Aug 19, 2026); they were never functional (no CMD / no pip install) and the README has always documented the venv flow as the supported setup. The venv flow above is the only supported path.

## Environment Configuration

All configuration comes from `.env` (see `.env.example`). Dev-critical keys:

| Variable | Dev value | Production |
|---|---|---|
| `SECRET_KEY` | any long random string (required) | required, strong |
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | empty (defaults to localhost) | `afrikaihajfonas.hu,www.afrikaihajfonas.hu` |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | `postgres://user:pass@host:5432/db` |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | `django.core.mail.backends.smtp.EmailBackend` (+ `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`) |
| `DEFAULT_FROM_EMAIL` | optional | `noreply@afrikaihajfonas.hu` |
| `CSRF_TRUSTED_ORIGINS` | not needed | `https://your-domain,...` (required for HTTPS POSTs) |
| `SECURE_SSL_REDIRECT` | n/a (DEBUG) | `True` default; set `False` if CDN/proxy redirects at edge |
| `SECURE_HSTS_SECONDS` | n/a (DEBUG) | `31536000` default |

With `DEBUG=False` the settings automatically enable HSTS, secure cookies, SSL redirect, proxy SSL header, nosniff, and referrer policy (see `specs/DEPLOYMENT.md`).

## Testing & Verification

```bash
# Full suite (explicit paths — root-level pytest doesn't discover apps/ tests)
python -m pytest apps/bookings/tests.py apps/site_config/tests.py apps/payments/tests.py \
                   apps/providers/tests.py apps/services/tests.py apps/users/tests.py config/tests.py

python manage.py check                    # 0 issues expected
python manage.py makemigrations --check   # "No changes detected" expected
python manage.py showmigrations           # 48 applied, 0 pending
```

Current state: **170/170 tests pass** (services 28, site_config 118, bookings 18, config 6; the `providers`/`users`/`payments` test modules are empty stubs); migration graph verified from a fresh database (migrate-from-zero succeeds; 48 applied migrations; seed data present: 4 payment methods, 24 email translations, 4 content blocks, 6 PageSEO, 1 GlobalSEO).

> Note on migration counts: the `payments` app was decommissioned early (Phase 0) and its 2 migrations intentionally deleted. The canonical count is **48** applied migrations across active apps.

## Management Commands & Cron

| Command | Recommended cadence | Purpose |
|---|---|---|
| `python manage.py expire_holds` | every 15 min | Expire past-due holds → `expired` + email |
| `python manage.py send_expiry_reminders` | every 30 min | Send 2h/1h reminder emails (idempotent) |

Both support `--dry-run`. No Celery — plain cron (examples in `specs/DEPLOYMENT.md`).

## Production Deployment

Full guide: **`specs/DEPLOYMENT.md`** (env vars, `.mo` compilation, `collectstatic`, gunicorn, nginx config, cron, troubleshooting, post-deploy checklist). Summary: PostgreSQL via `DATABASE_URL`, SMTP email backend, `collectstatic` to `staticfiles/` served by the proxy, `mediafiles/` served by the proxy (Django does not serve media when `DEBUG=False`), gunicorn behind nginx/Cloudflare terminating TLS.

## Branch Strategy

- **`main`** — the stable, production branch. All Phase 1–7 work is merged here (`ef16dc7`, Aug 17, 2026) and verified (170 tests, migration-integrity check, fresh-DB migrate).
- **`main4qp`** — the *former* integration branch used during parallel agent-driven development. Fully merged into `main`; kept only for history. New work should branch from `main`.
- Feature branches are deleted after merging.

## Implemented vs. Deferred

**Implemented and verified:** catalog + SHEIN-style detail page, full 4-step wizard with payments + snapshots, confirmation, guest lookup, admin dashboard + review/refund workflow, auto-expire + reminders, all 8 transactional emails, trilingual UI (341 strings ×3), admin-managed business content (7A–7E) **including public FAQ page + announcement banner rendering (Aug 19, 2026)**, SEO models + sitemap/robots/JSON-LD, production security settings, deployment guide.

**Known gaps / deferred (do not assume these work):**

1. **~~Catalog live filtering is broken~~ — FIXED (Aug 18, 2026):** `service_list.html` now loads the HTMX runtime (per-template include, same pattern as the wizard). Gender tabs and debounced search swap results via the `service_grid.html` partial; the native no-JS "Apply Filters" submit still works. Covered by `apps/services/tests.py`.
2. **~~Catalog gender matching is wrong~~ — FIXED (Aug 18, 2026, branch `feature/dynamic-parent-categories`):** the `name__icontains` lookup ("Men's Braids" matched "Women's Braids") was eliminated by making catalog tabs dynamic and ID-based (`?cat=<pk>`); the old `gender` name param was removed. See Decision #35.
3. **~~No public FAQ page~~ — FIXED (Aug 19, 2026):** the `FAQ` + `FAQTopic` models are now surfaced at `/faq/` (admin-managed topics grouping, trilingual with HU fallback, HTMX search, accordion, expand/collapse-all). Nav links point to the real page; sitemap includes it. See Decision #36.
4. **hreflang tags:** deferred (needs URL-based i18n).
5. **~~`settings.py` exempts `/health-check/` from SSL redirect but no such URL exists~~ — FIXED (Aug 19, 2026):** the dead `SECURE_REDIRECT_EXEMPT` entry was removed (no consumer; gunicorn/nginx serve directly). See Decision #36.
6. **~~`Dockerfile` is a stub; Docker flow is not supported~~ — FIXED (Aug 19, 2026):** the scaffold-era `Dockerfile` and `docker-compose.yml` were removed entirely (never functional: no CMD / no pip install; README has always documented the venv flow). See Decision #36.
7. **~~`media/` directory at repo root + seeded service images 404~~ — FIXED (Aug 19, 2026):** the legacy empty `media/` dir was removed, and the 4 dev `ServiceImage` rows were repointed to real tracked files in `mediafiles/`. Note: this is dev/demo data — in production the administrator manages service images; no permanent production ownership of the current demo images is claimed (Decision #36).
8. **~~Gender tab highlight goes stale after an HTMX swap~~ — FIXED (Aug 18, 2026, same branch):** `switchCategory()` now syncs the active pill classes client-side.
9. **Category labels are single-language (not a bug — documented):** dynamic category names are DB values rendered verbatim; they were effectively English-only before this change too (the old `{% trans %}` wrappers had no msgids in any `.po`). Multilingual category names = Category B translation pattern, deferred unless separately approved (Decision #35).

## Project Documentation

| Document | Purpose |
|---|---|
| `specs/MASTER_CONTEXT_AND_SPECS.md` | Source of truth: philosophy, models, business rules, journeys, URLs |
| `specs/ARCHITECTURAL_PRINCIPLES.md` | Business-managed content architecture (Phases 7A–7E), content categories, snapshots, emails, SEO |
| `specs/DECISIONS.md` | Decision log with rationale (#1–#35) |
| `specs/PROGRESS_HISTORY.md` | Phase-by-phase build history and verification results |
| `specs/EXECUTION_RULES.md` | Guardrails for builder agents |
| `specs/DEPLOYMENT.md` | Production deployment guide |
| `.docs/` | Original business documents (salon info, booking specification v10) |

---

License: MIT. © 2025–2026 Afrikai Hajfonás.
