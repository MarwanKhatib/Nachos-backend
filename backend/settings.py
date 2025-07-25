"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from datetime import timedelta
from pathlib import Path
import os

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)


ALLOWED_HOSTS = ["*"]

# CORS Settings for production
CORS_ALLOW_ALL_ORIGINS = True

# Allow credentials for Swagger UI
CORS_ALLOW_CREDENTIALS = True

# Allow all headers and methods for API testing
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET", 
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# CSRF settings for HTTPS
CSRF_TRUSTED_ORIGINS = ["*"]

# Security settings for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None
SECURE_SSL_REDIRECT = not DEBUG  # Force HTTPS in production, allow HTTP in debug
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "APIs",
    "rest_framework",
    # "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist", # Added for token blacklisting
    "corsheaders",
    "drf_yasg",  # Swagger documentation
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "APIs.middleware.request_logger_middleware.RequestLoggerMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS_ALLOWED_ORIGINS = [
#     "https://marwankhatib.github.io",
# ]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "ssl": (
                {"ssl": True}
                if config("DB_USE_SSL", default=False, cast=bool)
                else {}
            )
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True
APPEND_SLASH = True
FORCE_SCRIPT_NAME = "/"


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Add this for development
if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         "rest_framework.authentication.TokenAuthentication",
#         "rest_framework.authentication.SessionAuthentication",
#         "rest_framework.authentication.BasicAuthentication",
#     ],
#     "DEFAULT_PERMISSION_CLASSES": [
#         "rest_framework.permissions.AllowAny",
#     ],
# }


AUTH_USER_MODEL = "APIs.User"


# JWT Settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,  # Default page size
    "PAGE_SIZE_QUERY_PARAM": "page_size",  # Allow client to override page size
    "MAX_PAGE_SIZE": 100,  # Maximum page size allowed
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # Access token expires after 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # Refresh token expires after 1 day
}

# Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

# Add Swagger settings for JWT authentication
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
    "USE_SESSION_AUTH": False,
    "JSON_EDITOR": True,
    "SUPPORTED_SUBMIT_METHODS": [
        "get",
        "post",
        "put",
        "delete",
        "patch",
    ],
    "OPERATIONS_SORTER": "alpha",
    "TAGS_SORTER": "alpha",
    "DOC_EXPANSION": "none",
    "DEFAULT_MODEL_RENDERING": "example",
    "DEEP_LINKING": True,
    "SCHEMES": ["http", "https"] if DEBUG else ["https", "http"],  # Prioritize http for debug, https for production
    "DEFAULT_API_URL": "http://localhost:8000" if DEBUG else "https://nachos-backend-production.up.railway.app/",
}

# Public API URL for drf-yasg to correctly generate URLs
PUBLIC_API_URL = "http://localhost:8000" if DEBUG else "https://nachos-backend-production.up.railway.app/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "APIs": { # Logger for your application's custom logs
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "APIs.middleware.request_logger_middleware": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "": { # Root logger
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
