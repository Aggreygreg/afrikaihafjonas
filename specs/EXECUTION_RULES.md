# Afrikai Hajfonás — Execution Rules

**Last Updated:** August 17, 2026
**Purpose:** Guardrails for builder agents (hack_1, hack_2, hack_3, etc.) working on this project. These rules are non-negotiable.

---

## Builder Agent Rules

### 1. Atomic Tasks
- Maximum 4 files per modification
- Break larger tasks into sequential atomic steps
- Each atomic step should be independently verifiable
- If a task touches more than 4 files, split it

### 2. Commits
- Commit after every successful atomic task
- Conventional format: `feat(app): description`
- Examples:
  - `feat(bookings): add age validation to wizard step 3`
  - `fix(services): correct image switching logic for M2M options`
  - `docs(views): update guest lookup show/hide rules`
- Do NOT batch 10 different feature updates into one massive commit

### 3. Branching
- Feature branches fork from `main` (**updated Aug 17, 2026** — `main4qp` was merged and retired)
- Merge back into `main` when complete
- Delete feature branch after merge (clean repo)
- `main4qp` still exists but is history-only — do NOT target it

### 4. Security
- Fine-Grained PAT only (no root SSH keys)
- Never commit secrets, API keys, or credentials
- `.env` files in `.gitignore`

### 4.5. ⛔ HOST SAFETY — NEVER Kill Parent/System Processes

**This is the #1 rule. Violating it takes down the entire QwenPaw service and ALL agents.**

- **NEVER** run `Stop-Process`, `taskkill`, `pkill`, or any process-termination command on:
  - Any `python` / `python.exe` process
  - Any `uvicorn`, `gunicorn`, `django` server process
  - Any `node`, `qwenpaw`, or `cloudflared` process
  - ANY process you did not start yourself
- **NEVER** run `Stop-Process -Force` on ANYTHING without explicit user permission
- **NEVER** run system-modifying commands that affect the host OS, service registry, or network stack
- If a dev server (e.g., `runserver`) is already running on a port, **do not kill it** — use a different port or ask the manager
- If you need to restart or kill ANY process, **stop and ask the user first** — no exceptions
- The QwenPaw Python process IS the parent process running this agent. Killing it = killing yourself AND every other agent in the fleet

### 4.6. 🔀 Isolated Worktrees for Parallel Builders

**When multiple builder agents work on the same repo simultaneously, each MUST use its own git worktree.**

The main project directory (`C:\Users\Sabiedu\Projects\afrikai-hajfonas`) is shared across all agents. If two agents run `git checkout` in the same working tree, they clobber each other's uncommitted changes and commits land on the wrong branch.

**Standard workflow for every builder dispatch:**
1. Manager assigns a feature branch name (e.g., `feature/expiry-reminders`)
2. Builder creates an isolated worktree:
   ```
   git worktree add C:\Users\Sabiedu\Projects\<short-name> main4qp
   cd C:\Users\Sabiedu\Projects\<short-name>
   git checkout -b feature/<name>
   ```
3. All work happens inside the worktree — never in the main project dir
4. The venv (`.venv`) is shared — reference it from the main project dir
5. After merge, manager removes the worktree:
   ```
   git worktree remove C:\Users\Sabiedu\Projects\<short-name>
   ```
6. **NEVER** `git checkout` or `git stash` in the main project dir when another agent might be working — use your own worktree instead

**The main project dir is reserved for the manager's own work and the final `main4qp` checkout.**

---

## Business Logic Restraints

### 5. No Payment Gateways
- **NO** Stripe, PayPal, Barion, or any automated payment processing
- All payments are manual bank transfers (Revolut, Wise, TransferGo, Bank Transfer)
- Proof of payment is a screenshot upload, not an API callback

### 6. No Customer Reviews
- **NO** star ratings, comments, or review system
- The `apps.reviews` module was intentionally deleted
- Keep the platform lightweight and focused

### 7. No Client Accounts
- **NO** user registration, login, or password management
- Clients are anonymous consultation submitters
- Plain text fields: `client_name`, `client_email`, `client_phone`
- Admin filters `AppointmentRequest` table by email for customer history

### 8. Currency = HUF (Zero Decimals)
- Hungarian Forint with zero decimal places
- Format: `8,000 Ft` (not `8000.00 Ft`)
- Enforced everywhere: models, templates, admin
- `@property` methods for formatting, never template tags

### 9. i18n = Wrap Now, Translate Later (NOW FULLY BUILT)
- All template strings wrapped in `{% trans %}` ✅ (323 msgids)
- Translations complete: HU/EN/DE `.po` files tracked; `.mo` are build artifacts — after a fresh clone run `_build_po.py` → `_apply_translations.py` → `_compile_mo.py` (polib, no gettext needed)
- Language switching: `django_language` cookie + `/i18n/setlang/` (first-visit modal in `base.html`); no URL prefixes
- New UI strings: wrap in `{% trans %}` immediately, add msgids to all 3 `.po` files, keep msgids in English

### 10. Fat Models, Skinny Templates
- All business logic in Django model `@property` methods or `utils.py`
- Templates are for display only — no math, formatting, or business rules
- Makes logic testable and prevents duplication

### 11. No Provider Logins/Dashboards
- Stylists do not log in
- All reviews and approvals are handled by the Admin/Owner
- Do not implement complex Role-Based Access Control (RBAC)

### 12. No Automated SMS Notifications
- Do not integrate Twilio or SMS APIs
- Communication is strictly via Email

### 13. No Multi-Location/Tenant Logic
- Do not build models mapping to different salon addresses
- Single salon, single location

---

## HTMX Rules

### 14. No `window.location.reload()`
- Never use brute-force JS reloads
- Use `hx-swap` and DOM targeting for all updates
- Exception: only for total state reset (should be extremely rare)

### 15. `hx-target` IDs Must Match
- IDs of returned partials must perfectly match `hx-target` values
- Test every HTMX interaction before marking complete

### 16. Maintain Flow State
- Each wizard step targets the same container (`#wizard-content`)
- Session state persists across HTMX swaps
- Back buttons restore previous step without losing data

---

## Quality Gates

### 17. Manager Verifies Everything
- "I don't trust 'done'" — always verify output
- Check: files exist, not boilerplate, migrations succeed, server runs
- Verify acceptance criteria before moving to next phase
- User reviews at checkpoints — no pushing to main without go-ahead

### 18. One Dispatch Per Phase
- One consolidated dispatch per phase
- Follow-up messages cancel running tasks
- Wait for completion and verification before next dispatch

### 19. Timeout Management
- Builder timeout: 30-40 minutes (not 20 — too short for full-stack builds)
- If agent times out, check what was actually built before re-dispatching
- Some agents report finished with zero files produced — always verify

---

## File Organization

### 20. Photo Upload Paths
- Hair photos: `MEDIA_ROOT/hair_photos/` (flat — no AFH reference subfolders)
- Proof of payment: `MEDIA_ROOT/payment_proofs/` (flat)
- Paths are intentionally flat for now. AFH reference subfolders are a future optimization, not a current concern.
- Files retained indefinitely (no auto-deletion)

### 21. Template Structure
- Base template: `base.html` (nav, footer, Tailwind CDN)
- Wizard container: `consult_wizard.html` (progress bar + `#wizard-content`)
- Step partials: `wizard_step_1.html`, `wizard_step_2.html`, etc.
- Each step partial targets `#wizard-content` via HTMX

---

## HICLAW Builder Agent Context

**Who you are:** You are a builder agent (hack_1, hack_2, or hack_3) working on the Afrikai Hajfonás project. You are a full-stack engineer specializing in Django + HTMX + Tailwind CSS.

**Your Manager:** HICLAW coordinates the project. You receive atomic tasks with acceptance criteria. You execute, commit, and report back. You do NOT make architectural decisions — those are in DECISIONS.md.

**The Repo:** `https://github.com/Aggreygreg/afrikaihafjonas` (public)
**Branch:** `main4qp` (integration branch). Feature branches fork from here.
**Local path:** `C:\Users\Sabiedu\Projects\afrikai-hajfonas`
**Venv:** `.venv` (Python 3.12.12, Django 4.2.25) — shared, always at the main project dir
**Database:** SQLite (dev)
**Superuser:** admin / admin123

**MANDATORY: Worktree isolation (see Rule 4.6)**
When dispatched, your manager will give you a worktree path. Work ONLY inside your worktree. NEVER run `git checkout` in the main project dir.
```
git worktree add C:\Users\Sabiedu\Projects\<short-name> main4qp
cd C:\Users\Sabiedu\Projects\<short-name>
git checkout -b feature/<name>
# Use the shared venv: C:\Users\Sabiedu\Projects\afrikai-hajfonas\.venv\Scripts\python.exe
```

**Before starting any task:**
1. Read `MASTER_CONTEXT_AND_SPECS.md` — the full spec
2. Read `PROGRESS_HISTORY.md` — where the project is now
3. Read `DECISIONS.md` — why things are built this way
4. Read this file (`EXECUTION_RULES.md`) — your guardrails

**After completing any task:**
1. Run `python manage.py makemigrations --check` — must say "No changes detected"
2. Run `python manage.py check` — must say "0 issues"
3. Run `python manage.py test` if tests exist
4. Commit with conventional format
5. Report what was built, what files changed, any issues encountered

**Known gotchas:**
- Django's interactive `makemigrations` prompt can trip agents in non-interactive shells. Use `--noinput` with pre-specified defaults when needed.
- `JSONField` on SQLite works fine for dev but needs PostgreSQL for prod.
- `ImageField` requires `Pillow` (already installed in venv).
- The old `Booking` model no longer exists. All references must use `AppointmentRequest`.
- `proof_of_payment` and `payment_method` MUST be set to `blank=True` in Phase 4 — the model currently has neither as blank. Step 3 creates the record before payment data exists, so both fields need `blank=True`. This is a Phase 4 task, not existing state.
- Upload paths are FLAT for now (`hair_photos/`, `payment_proofs/`) — no AFH reference subfolders. That's a future optimization, not a Phase 4 concern.

---

## Anti-Patterns (Strict)

1. **NO** third-party payment gateways
2. **NO** customer reviews
3. **NO** `window.location.reload()` in HTMX
4. **NO** fat templates
5. **NO** unverified migrations
6. **NO** client accounts
7. **NO** decimal currency
8. **NO** Celery (use management commands + cron)
9. **NO** SMS integrations
10. **NO** multi-tenant logic
11. **NO** process-termination commands (`Stop-Process`, `taskkill`, `pkill`) on ANY process you didn't start — see Rule 4.5

---

## Known Gotchas / Open Issues (as of Aug 17, 2026)

Read before touching these areas — do not "discover" them the hard way:

1. **HTMX is NOT loaded globally.** The `<script src="unpkg.com/htmx.org@1.9.12">` include exists only in `consult_wizard.html`, `wizard_step_3.html`, `wizard_step_4.html`. `service_list.html` uses `hx-get` + calls `htmx.trigger()` **without loading the library** — catalog live filtering (gender tabs, debounced search) is non-functional; native form submit still works. If you build a new HTMX page, include the script on THAT template.
2. **Tailwind is loaded via CDN** (`cdn.tailwindcss.com` in `base.html`). The `theme/` + `django-tailwind` build chain exists but its compiled CSS is not committed or referenced; `static/` only has a `.gitkeep`. Dev setup needs NO npm.
3. **Docker is not real.** `Dockerfile` is a stub (env vars + WORKDIR only, no pip install/CMD). Supported setup = venv (see README).
4. **Dead config:** `SECURE_REDIRECT_EXEMPT` lists `/health-check/` but no such URL exists. Harmless; remove if you add a health-check route.
5. **No public FAQ page** — `FAQ`/`FAQTranslation` models + admin exist; nav "FAQs" links are `#faq`/`#` placeholders. Build the view/template before pointing nav links at it.
6. **Canonical migration count = 47.** The two `payments` migrations were intentionally deleted at decommission (`e2687c8`); `apps/payments/` is an empty shell kept only to avoid import errors.
7. **Windows console:** run Python with `set "PYTHONIOENCODING=utf-8"` (cp1252 default mangles HU/DE text); wrap cmd `set` values in quotes.
8. **Pytest:** always pass explicit test file paths (e.g. `pytest apps/bookings/tests.py`), not bare `pytest`.
9. **Locked dev DB:** if `db.sqlite3` is held by another process, don't move it — run tests/migrations against a temp DB via `DATABASE_URL=sqlite:///db_fresh_test.sqlite3`.
10. **Uploads are flat:** `MEDIA_ROOT/hair_photos/` and `MEDIA_ROOT/payment_proofs/` — no per-app subdirectories (Rule 20).
