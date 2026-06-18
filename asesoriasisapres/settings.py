import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'core',
    'leads',
]

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'asesoriasisapres.urls'

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
                'core.context_processors.seo_defaults',
            ],
        },
    },
]

WSGI_APPLICATION = 'asesoriasisapres.wsgi.application'

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

db_name = os.environ.get('DB_NAME', '')
if db_name:
    db_engine = os.environ.get('DB_ENGINE', 'mysql')
    if db_engine == 'mysql':
        _engine_path = 'django.db.backends.mysql'
        _default_port = '3306'
    else:
        _engine_path = 'django.db.backends.postgresql'
        _default_port = '5432'
    DATABASES = {
        'default': {
            'ENGINE': _engine_path,
            'NAME': db_name,
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', _default_port),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'static_collected'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHE_MIDDLEWARE_SECONDS = 600
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

TAWKTO_ID = os.environ.get('TAWKTO_ID', '')

# Content Security Policy
CSP_DEFAULT_SRC     = ("'self'",)
CSP_SCRIPT_SRC      = ("'self'", "'unsafe-inline'", "https://embed.tawk.to", "https://va.tawk.to")
CSP_STYLE_SRC       = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://embed.tawk.to")
CSP_FONT_SRC        = ("'self'", "https://fonts.gstatic.com", "https://embed.tawk.to")
CSP_IMG_SRC         = ("'self'", "data:", "https:")
CSP_CONNECT_SRC     = ("'self'", "https://*.tawk.to", "wss://*.tawk.to")
CSP_FRAME_SRC       = ("'self'", "https://tawk.to", "https://*.tawk.to")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI        = ("'self'",)
CSP_FORM_ACTION     = ("'self'",)

# Proxy SSL (Cloudflare → Render): Django lee X-Forwarded-Proto para saber que es HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Dominos confiados para CSRF (requerido en Django 4.0+ detrás de proxy)
CSRF_TRUSTED_ORIGINS = [
    'https://asesoriasisapres.com',
    'https://www.asesoriasisapres.com',
    'https://asesoriasisapre.onrender.com',
]

# Seguridad en producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    # CSRF_COOKIE_HTTPONLY debe ser False (default) para que JS pueda leer
    # el token vía document.cookie y enviarlo en X-CSRFToken (AJAX)
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
