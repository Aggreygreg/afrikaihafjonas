import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file located at the project root
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# ALLOWED_HOSTS — comma-separated list from env. Filter out empty strings.
_allowed_hosts = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
ALLOWED_HOSTS = _allowed_hosts or ["localhost", "127.0.0.1"]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',

    # 3rd Party Apps
    'tailwind',
    'theme', # Tailwind theme app
    'django_htmx',
    'solo', # For site configuration
    'django_summernote', # WYSIWYG editor for admin content (Decision #33)

    # Local Apps
    'apps.users',
    'apps.services',
    'apps.providers',
    'apps.bookings',
    # 'apps.payments',  # DECOMMISSIONED — manual bank transfers only
    # 'apps.reviews',
    'apps.site_config', # New config app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_htmx.middleware.HtmxMiddleware", # HTMX middleware
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Point to the root templates/ folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.site_config.context_processors.site_config', # Custom context processor
                'apps.site_config.context_processors.seo', # SEO metadata (Phase 7E)
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# The database is now configured via the DATABASE_URL in your .env file
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=False)
}

# Email backend — console for dev, SMTP for production.
# Set EMAIL_BACKEND in .env to 'django.core.mail.backends.smtp.EmailBackend' for prod.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@afrikaihajfonas.hu")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'hu'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('hu', 'Magyar'),
    ('en', 'English'),
    ('de', 'Deutsch'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']


# # Static files (CSS, JavaScript, Images)
# STATIC_URL = 'static/'
# # Point to the root static/ folder for project-wide static files
# STATICFILES_DIRS = [ BASE_DIR / "static" ]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = 'static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
STATIC_ROOT = BASE_DIR / "staticfiles"

# CSRF trusted origins — needed for HTTPS POST requests from the production domain.
# Comma-separated, e.g., "https://afrikaihajfonas.hu,https://www.afrikaihajfonas.hu"
_csrf_origins = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
CSRF_TRUSTED_ORIGINS = _csrf_origins

# Media files (User-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Tailwind CSS settings
TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = [ "127.0.0.1", ]

# Path to npm executable for Django Tailwind
NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"
# ── django_summernote migration fix ───────────────────────────
# django_summernote 0.8.20 ships with old AutoField but our project uses
# BigAutoField. Override the migration module to a project-controlled dir
# so the generated migration is tracked in git, not lost in the venv.
MIGRATION_MODULES = {
    'django_summernote': 'config.summernote_migrations',
}

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# ── Summernote WYSIWYG (Decision #33) ──────────────────────────
# Limited toolbar — salon owner is not a web developer.
# Used for: FAQ answers, ContentBlock bodies, Announcement messages.
# NOT used for email templates (those are plain text / plain HTML).
SUMMERNOTE_CONFIG = {
    "summernote": {
        "width": "100%",
        "height": "300",
        "toolbar": [
            ["style", ["bold", "italic", "underline"]],
            ["para", ["ul", "ol", "paragraph"]],
            ["insert", ["link"]],
            ["view", ["fullscreen", "codeview"]],
        ],
    },
}


# ── Production security settings ──────────────────────────────
# These activate automatically when DEBUG=False. In dev (DEBUG=True)
# they are left at Django defaults so local HTTP development is unaffected.
if not DEBUG:
    # Force HTTPS for all requests.
    # Disable if your front proxy/CDN (Cloudflare, etc.) handles SSL redirect
    # at the edge — set SECURE_SSL_REDIRECT=False in .env.
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_REDIRECT_EXEMPT = [r"^/health-check/?$"]

    # HSTS — tells browsers to always use HTTPS
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Secure cookies — only sent over HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Content type sniffing protection
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

    # Referrer policy
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

    # Trust the X-Forwarded-Proto header from the reverse proxy
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")