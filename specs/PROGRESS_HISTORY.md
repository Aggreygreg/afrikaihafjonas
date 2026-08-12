# Afrikai Hajfonás — Progress History

**Last Updated:** August 11, 2026

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
| `services` | ✅ Complete | Suitability fields, M2M images, SHEIN detail page, discount engine |
| `bookings` | ✅ Functional | AppointmentRequest model, wizard Steps 1-4, confirmation, guest lookup all working |
| `payments` | 🗑️ Decommissioned | Dead weight removed in Phase 0 |
| `providers` | ✅ Stable | Stylists + weekly availability |
| `site_config` | ✅ Stable | Singleton config + context processor |
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

## What's Left After Phase 4

- **Phase 5:** Admin dashboard customization (queues, approval workflow, refund processing)
- **Phase 6:** Background tasks + polish (expiry reminders, console email, management commands)
- **Final Polish:** Static pages (About, etc.), language preference popup, full i18n translation files

---

## Session Management Policy (for HICLAW)

**Context windows fill up.** When working on a long project like this, sessions accumulate context. Here's the policy:

- If your context window is getting full (above ~70%), start a fresh session for the next phase.
- The specs are in the repo — re-read them in the new session.
- Don't force through a big phase on a half-full context — quality degrades.
- Starting fresh is NOT failure. It's good practice.
- Each new session should re-read: this file (PROGRESS_HISTORY.md), MASTER_CONTEXT_AND_SPECS.md, and DECISIONS.md.
