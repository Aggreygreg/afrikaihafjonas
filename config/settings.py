import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file located at the project root
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
# The SECRET_KEY is now loaded from your .env file
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# The DEBUG flag is now controlled by your .env file
DEBUG = os.environ.get("DEBUG", "False") == "True"

# ALLOWED_HOSTS is now controlled by your .env file
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

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

# Email — Console backend for dev (prints to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@afrikaihajfonas.hu'


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