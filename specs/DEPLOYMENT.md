# Afrikai Hajfonás — Production Deployment Guide

**Last Updated:** August 13, 2026

This document covers the steps required to deploy the application from a
clean clone to a production server.

---

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- A reverse proxy (nginx, Caddy, or Cloudflare Tunnel) terminating TLS
- `gettext` installed on the server (for `.mo` compilation)

---

## Step 1: Clone & Install Dependencies

```bash
git clone <repo-url> afrikai-hajfonas
cd afrikai-hajfonas
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

> **requirements.txt** is pip-compile output. It pins exact versions of
> all dependencies including `bleach` and `django-summernote`.

---

## Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set **all** required values:

| Variable | Required | Example |
|---|---|---|
| `SECRET_KEY` | ✅ | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | ✅ | `False` |
| `ALLOWED_HOSTS` | ✅ | `afrikaihajfonas.hu,www.afrikaihajfonas.hu` |
| `DATABASE_URL` | ✅ | `postgres://user:pass@localhost:5432/afrikai` |
| `EMAIL_BACKEND` | ✅ | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | If SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | If SMTP | `587` |
| `EMAIL_HOST_USER` | If SMTP | `noreply@afrikaihajfonas.hu` |
| `EMAIL_HOST_PASSWORD` | If SMTP | *(app password)* |
| `EMAIL_USE_TLS` | If SMTP | `True` |
| `DEFAULT_FROM_EMAIL` | Recommended | `noreply@afrikaihajfonas.hu` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | `https://afrikaihajfonas.hu,https://www.afrikaihajfonas.hu` |
| `SECURE_HSTS_SECONDS` | Optional | `31536000` (1 year, default) |

---

## Step 3: Compile Translations (.mo files)

`.mo` files are gitignored. Compile from `.po` files before starting the server:

**Option A — GNU gettext (preferred on Linux):**
```bash
django-admin compilemessages
```

**Option B — polib script (if gettext not available):**
```bash
python _compile_mo.py
```

---

## Step 4: Database Migration

```bash
python manage.py migrate
```

This runs all migrations including seed data:
- 4 payment methods (Revolut, Wise, TransferGo, Bank Transfer)
- 8 email templates × 3 languages = 24 translations
- 4 ContentBlocks (about, terms, privacy, about_mission)
- 6 PageSEO entries for static pages
- 1 GlobalSEO singleton

---

## Step 5: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

Output goes to `staticfiles/` (gitignored). Serve these via your reverse
proxy (nginx `alias` or Caddy `file_server`).

---

## Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

---

## Step 7: Start the Application Server

Using gunicorn:

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

Configure your reverse proxy to:
1. Terminate TLS (HTTPS)
2. Forward to `127.0.0.1:8000`
3. Set `X-Forwarded-Proto: https` header
4. Serve `staticfiles/` directly (don't proxy to gunicorn)
5. Serve `mediafiles/` directly (user uploads — hair photos, payment proofs)

---

## Reverse Proxy Example (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name afrikaihajfonas.hu www.afrikaihajfonas.hu;

    # SSL cert (managed by certbot or your provider)
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Static files
    location /static/ {
        alias /path/to/afrikai-hajfonas/staticfiles/;
    }

    # Media files (user uploads)
    location /media/ {
        alias /path/to/afrikai-hajfonas/mediafiles/;
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name afrikaihajfonas.hu www.afrikaihajfonas.hu;
    return 301 https://$host$request_uri;
}
```

---

## Post-Deploy Verification

1. Visit the homepage — hero section, language popup, service grid render.
2. Browse a service detail page — gallery, options, dynamic image switching.
3. Start the consultation wizard — Steps 1→4, submit test appointment.
4. Check admin dashboard at `/admin/` — all widgets populate.
5. Verify `/sitemap.xml` and `/robots.txt` are accessible.
6. Test Guest Lookup with the reference code from step 3.
7. Check email delivery — submit a test appointment and verify the
   `request_received` email arrives.

---

## Cron Jobs (Management Commands)

| Command | Frequency | Purpose |
|---|---|---|
| `python manage.py expire_holds` | Every 15 min | Expire past-due appointment holds, send `appointment_expired` email |
| `python manage.py send_expiry_reminders` | Every 30 min | Send 2h/1h reminder emails before hold expiry |

Example crontab:
```cron
*/15 * * * * cd /path/to/afrikai-hajfonas && .venv/bin/python manage.py expire_holds
*/30 * * * * cd /path/to/afrikai-hajfonas && .venv/bin/python manage.py send_expiry_reminders
```

---

## Production Settings (Automatic)

When `DEBUG=False`, the following security settings activate automatically:

- `SECURE_SSL_REDIRECT = True` — forces HTTPS
- `SESSION_COOKIE_SECURE = True` — cookies only over HTTPS
- `CSRF_COOKIE_SECURE = True` — CSRF cookie only over HTTPS
- `SECURE_HSTS_SECONDS = 31536000` — HSTS 1 year
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
- `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`

---

## Troubleshooting

**Emails not sending:** Verify `EMAIL_BACKEND` is set to SMTP in `.env`.
The console backend (dev) prints to stdout and does not send real emails.

**CSRF verification failed (403):** Ensure `CSRF_TRUSTED_ORIGINS` includes
your production domain with `https://` prefix.

**Static files 404:** Run `collectstatic` and configure your reverse proxy
to serve the `staticfiles/` directory directly (not through gunicorn).

**Translation not working:** `.mo` files are missing. Run `compilemessages`
or `_compile_mo.py`.
