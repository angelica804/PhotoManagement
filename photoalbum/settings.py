"""Production-ready Django settings for the Photo Album Management System."""

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DJANGO_ENV = os.getenv('DJANGO_ENV', 'development').lower()
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')

if DJANGO_ENV == 'production' and not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY must be set in production.')

SECRET_KEY = SECRET_KEY or 'dev-only-insecure-key'


def _is_postgres_scheme(scheme: str) -> bool:
    return scheme.lower().startswith(('postgres', 'postgresql'))


def _normalize_allowed_host(host: str) -> str:
    host = host.strip()
    if host.startswith('*.'):
        return '.' + host[2:]
    return host

ALLOWED_HOSTS = [
    _normalize_allowed_host(host)
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',')
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',') if origin.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'cloudinary',
    'django.contrib.staticfiles',
    'albums',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'photoalbum.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'albums.context_processors.is_album_admin',
            ],
        },
    },
]

WSGI_APPLICATION = 'photoalbum.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')

if DJANGO_ENV == 'production' and not DATABASE_URL:
    raise ImproperlyConfigured('DATABASE_URL must be set in production.')

if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    if not _is_postgres_scheme(parsed.scheme):
        raise ImproperlyConfigured('Unsupported database scheme in DATABASE_URL.')
    if not parsed.path or parsed.path == '/':
        raise ImproperlyConfigured('DATABASE_URL must include a database name.')
    if not parsed.username or not parsed.password:
        raise ImproperlyConfigured('DATABASE_URL must include a username and password.')
    if not parsed.hostname:
        raise ImproperlyConfigured('DATABASE_URL must include a database host.')

    db_options = {
        key: value
        for key, value in parse_qsl(parsed.query)
        if value
    }

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path[1:],
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or 5432,
        }
    }


    if db_options:
        DATABASES['default']['OPTIONS'] = db_options
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
cloudinary_credentials = [
    os.getenv('CLOUDINARY_CLOUD_NAME'),
    os.getenv('CLOUDINARY_API_KEY'),
    os.getenv('CLOUDINARY_API_SECRET'),
]
CLOUDINARY_CONFIGURED = bool(CLOUDINARY_URL or all(cloudinary_credentials))

DEFAULT_FILE_STORAGE = (
    'cloudinary_storage.storage.MediaCloudinaryStorage'
    if CLOUDINARY_CONFIGURED
    else 'django.core.files.storage.FileSystemStorage'
)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

if DJANGO_ENV == 'production' and not CLOUDINARY_CONFIGURED:
    import warnings

    warnings.warn(
        'Cloudinary is not configured in production. Falling back to local media storage.',
        RuntimeWarning,
    )

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = DEBUG is False and DJANGO_ENV == 'production'
SESSION_COOKIE_SECURE = DEBUG is False
CSRF_COOKIE_SECURE = DEBUG is False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
