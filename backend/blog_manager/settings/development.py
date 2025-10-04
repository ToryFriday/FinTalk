"""
Development settings for blog_manager project.
"""

from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='blog_manager_dev'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

# Allow additional origins from environment variable
CORS_ADDITIONAL_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
if CORS_ADDITIONAL_ORIGINS and CORS_ADDITIONAL_ORIGINS != ['']:
    CORS_ALLOWED_ORIGINS.extend(CORS_ADDITIONAL_ORIGINS)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

# Add additional CSRF trusted origins from environment variable
CSRF_ADDITIONAL_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',')
if CSRF_ADDITIONAL_ORIGINS and CSRF_ADDITIONAL_ORIGINS != ['']:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in CSRF_ADDITIONAL_ORIGINS if origin.strip()])

# Security settings for development (less restrictive)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Cookie settings for development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Additional development settings
INTERNAL_IPS = [
    '127.0.0.1',
    '0.0.0.0',
]

# Development-specific logging
LOGGING['loggers']['corsheaders'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}