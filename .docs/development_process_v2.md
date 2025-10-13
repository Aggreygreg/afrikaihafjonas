# Development Process v2
**Project:** Hairstyle Booking Platform  
**Version:** 2.0 (Refined After Gemini Review)  
**Status:** Approved and Ready for Execution  
**Date:** 2025-10-13

---

## Overview

This document outlines the **refined, professional, and simplified development workflow** for the Hairstyle Booking Platform project. It integrates Gemini’s feedback to ensure a process that is both **efficient for a solo developer** and **robust enough for future scalability**.  
The goal is to reduce unnecessary complexity, follow modern Django best practices, and prevent future development errors.

---

## 1. Project Management & Workflow

### 1.1 Version Control Strategy — *Simplified GitHub Flow*
For a solo developer, we adopt **GitHub Flow** instead of full GitFlow. This keeps things lean, while maintaining professional discipline.

**Branches:**
- `main` — The production-ready branch. Must always remain stable.
- `feature/<name>` — Each new feature or bug fix starts here (e.g., `feature/booking-system`).
- Optional: `hotfix/<name>` for urgent production fixes.

**Workflow:**
1. Create a new branch from `main`.
2. Develop and commit regularly with descriptive messages.
3. Push to GitHub and open a Pull Request into `main`.
4. Review and merge once tested locally and all CI checks pass.

✅ **Why this approach:** Simpler than GitFlow but still structured, perfect for solo or small-team development.

---

## 2. Project & File Structure

A clean and maintainable layout ensures scalability and avoids Django’s “app explosion.”

```
afrikaihafjonas/
│
├── .docs/                      # Documentation and specs
│   └── Hairstyle_Booking_Specification_v10.0.md
│
├── config/                     # Core Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py                # NEW: Homepage view can live here
│   └── wsgi.py
│
├── apps/                       # Directory for modular Django apps
│   ├── bookings/
│   ├── services/
│   ├── providers/
│   ├── users/
│   └── reviews/
│
├── static/                     # Global static files (CSS, JS, images)
├── templates/                  # Global templates folder
│
├── venv/                       # Virtual environment (ignored by Git)
├── manage.py
├── requirements.in             # Base dependency list (human-edited)
├── requirements.txt            # Auto-generated pinned dependencies
├── .gitignore
├── LICENSE
└── README.md
```

✅ **Why this layout:** Balanced between modularity and simplicity — supports clean scaling and direct deployment.

---

## 3. Dependency Management — Using `pip-tools`

Instead of manually managing or freezing dependencies, use **pip-tools** for deterministic builds.

### Steps:
1. Add top-level dependencies to `requirements.in`:
   ```
   django
   psycopg2-binary
   python-dotenv
   gunicorn
   django-tailwind
   ```
2. Compile pinned versions:
   ```bash
   pip install pip-tools
   pip-compile requirements.in
   ```
3. Install:
   ```bash
   pip install -r requirements.txt
   ```

✅ **Why:** Keeps the environment reproducible, prevents dependency drift, and ensures easy updates.

---

## 4. Environment Configuration

Use **dotenv** for secrets and configuration management.

Create `.env`:
```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/afrikaihafjonas
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_key
```

✅ **Why:** Prevents accidental credential leaks and allows smooth environment changes between local and production.

---

## 5. Frontend Setup — Django + Tailwind + HTMX

Use **django-tailwind** for seamless Tailwind integration and **HTMX** for lightweight interactivity.

### Commands:
```bash
python manage.py tailwind init
python manage.py tailwind install
```

Tailwind files will live under `theme/static_src/`.  
HTMX will be included in base templates to handle dynamic UI updates.

✅ **Why:** Gives modern frontend power without needing React or Node.js complexity.

---

## 6. Testing Strategy

A professional testing setup prevents regressions and ensures confidence before deployment.

### Levels of Testing:
- **Unit Tests:** For core logic (e.g., availability checks, booking rules).
- **Integration Tests:** Verify booking/payment/email flows.
- **E2E Tests:** Use **Playwright** for UI flow testing (booking and checkout).
- **Security & Accessibility:** Run `bandit` for vulnerabilities and `axe-core`/`Lighthouse` for accessibility.

### Example Commands:
```bash
python manage.py test
pytest --cov=apps
```

✅ **Why:** Maintains reliability and professional quality standards.

---

## 7. Continuous Integration (CI)

### 7.1 GitHub Actions Workflow
A simple `.github/workflows/django.yml` pipeline will:

1. Install dependencies.
2. Run tests.
3. Build Docker image to ensure deployability.
4. Lint and check migrations.

### 7.2 Example CI Environment Variables:
```
DJANGO_SETTINGS_MODULE=config.settings
DATABASE_URL=postgres://postgres:postgres@localhost:5432/testdb
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

✅ **Why:** Ensures every push to `main` is production-safe.

---

## 8. Continuous Deployment (CD)

Deployment will initially use **Render** or **Railway**, with Dockerized configuration for scalability.

### 8.1 Dockerfile Outline:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 8.2 Docker Compose (for local testing):
```yaml
version: "3"
services:
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: afrikaihafjonas
    ports:
      - "5432:5432"
```

✅ **Why:** Ensures local and production environments behave identically.

---

## 9. Code Quality & Linting

### Tools:
- **Black** – Auto-formatting
- **Flake8** – Linting
- **isort** – Import sorting
- **Bandit** – Security scanning

### Example Commands:
```bash
black .
flake8 .
isort .
bandit -r .
```

✅ **Why:** Keeps the codebase readable, consistent, and secure.

---

## 10. Phased Development Roadmap

| Phase | Deliverables | Tools / Focus |
|-------|--------------|---------------|
| **Phase 1: Core Setup** | Project scaffold, CI/CD setup, DB integration | Django + PostgreSQL |
| **Phase 2: Core Features** | User auth, service CRUD, booking flow | Django Views + HTMX |
| **Phase 3: Payments** | Stripe/PayPal integration, email notifications | Django + Stripe SDK |
| **Phase 4: Admin Dashboard** | Provider management, reports, content edit tools | Django Admin |
| **Phase 5: Testing & PWA** | Playwright, caching, service worker setup | Tailwind + PWA tools |
| **Phase 6: Launch & Optimize** | Deployment, monitoring, backups | Docker + Render |

✅ **Why:** Structured around deliverable milestones rather than arbitrary deadlines.

---

## 11. Backup, Monitoring, and Maintenance

- **Daily automated backups** via host provider.
- **Error monitoring** using Sentry.
- **Logging** via Django’s built-in logging + rotation.
- **Security updates** monthly via `pip-compile --upgrade`.

---

## 12. Documentation & Handoff

All documentation (e.g., specifications, setup guides, API docs) will live in `.docs/`.  
Future developers can onboard easily with README + environment setup instructions.

---

## ✅ Final Notes
This refined process is tailored for solo development while adhering to professional-grade practices.  
It ensures you can develop, test, and deploy confidently with minimal risk of errors or rework.
