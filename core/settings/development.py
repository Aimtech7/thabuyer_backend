"""
core/settings/development.py - Local development settings
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0'])

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# Frontend URL for verification links
FRONTEND_URL = "http://localhost:8080"

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/0')],
        },
    },
}

# JWT Security
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'my-app-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'my-refresh-token',
    'JWT_AUTH_SECURE': False,
    'JWT_AUTH_SAMESITE': 'Lax',
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Paystack Test Keys (from env)
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY', default='sk_test_fake')
PAYSTACK_PUBLIC_KEY = env('PAYSTACK_PUBLIC_KEY', default='pk_test_fake')
PAYSTACK_CALLBACK_URL = f"{FRONTEND_URL}/payment/success"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
