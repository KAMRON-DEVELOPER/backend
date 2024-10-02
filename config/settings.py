from datetime import timedelta
from pathlib import Path
import environ


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
# Todo: remove when using docker env_file
environ.Env.read_env(BASE_DIR / ".env")


SECRET_KEY = env.str("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


print("ALLOWED_HOSTS <*> ", ALLOWED_HOSTS)


INSTALLED_APPS = [
    'jazzmin',
    'daphne',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    'adrf',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'storages',
    'channels',
    'django_celery_beat',

    'shared_app',
    'users_app',
    'community_app',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "users_app.CustomUser"

USE_REDIS_CHANNEL_LAYER = env.bool("USE_REDIS_CHANNEL_LAYER", default=False)
USE_REDIS_FOR_CACHE = env.bool("USE_REDIS_FOR_CACHE", default=False)
USE_SQLITE3 = env.bool("USE_SQLITE3", default=True)
USE_DATABASE_URL = env.bool("USE_DATABASE_URL", default=False)

JAZZMIN_SETTINGS = {
    "site_title": "Kronk Admin",
    "site_header": "Kronk API",
    "welcome_sign": "Welcome to the Kronk API",
}

# ! CACHES
if USE_REDIS_FOR_CACHE:
    REDIS_CACHE_HOST = env.str('REDIS_CACHE_HOST', default='127.0.0.1')
    REDIS_CACHE_PORT = env.int('REDIS_CACHE_PORT', default=6379)
    REDIS_LOCATION = f"redis://{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}"
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_LOCATION,
            "TIMEOUT": env.float("REDIS_CACHE_TIMEOUT", default="300"),
        }
    }

    # Celery configurations
    CELERY_BROKER_URL = REDIS_LOCATION
    CELERY_TIMEZONE = env.str("CELERY_TIMEZONE", default="")
    CELERY_TASK_TIME_LIMIT = env.float("CELERY_TASK_TIME_LIMIT")
    CELERY_TASK_TRACK_STARTED = env.bool("CELERY_TASK_TRACK_STARTED", default=True)
    CELERY_CACHE_BACKEND = "default"
    CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"  # create periodic tasks in admin panel

# ! Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "NON_FIELD_ERRORS_KEY": "detail",
}

# ! Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": "Bearer",  # also have other options ("JWT", "Bearer", "Token")
}

# ! Channel Layer
if USE_REDIS_CHANNEL_LAYER:
    REDIS_CACHE_HOST = env.str('REDIS_CACHE_HOST', default='127.0.0.1')
    REDIS_CACHE_PORT = env.int('REDIS_CACHE_PORT', default=6379)
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(REDIS_CACHE_HOST, REDIS_CACHE_PORT)],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

# ! Database
if USE_SQLITE3:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }
else:
    if USE_DATABASE_URL:
        DATABASES = {
            "default": env.db(),
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": env.str("POSTGRES_DB", default=""),
                "USER": env.str("POSTGRES_USER", default=""),
                "PASSWORD": env.str("POSTGRES_PASSWORD", default=""),
                "HOST": env.str("POSTGRES_HOST", default=""),
                "PORT": env.str("POSTGRES_PORT", default=""),
            },
        }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/


STORAGE_DESTINATION = env.str("STORAGE_DESTINATION", default="")


if STORAGE_DESTINATION == "local":
    print("USE LOCAL STORAGE")
    STATIC_URL = "/static/"
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

if STORAGE_DESTINATION == "s3":
    AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default="")
    AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="")
    AWS_QUERYSTRING_EXPIRE = 604800
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

    AWS_CUSTOM_DOMAIN = "https://s468.s3-cdn-clients.arviol.com"

    MEDIA_LOCATION = "media/"
    STATICFILES_LOCATION = "staticfiles/"

    STATIC_URL = f"{AWS_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}"
    MEDIA_URL = f"{AWS_CUSTOM_DOMAIN}/{MEDIA_LOCATION}"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": MEDIA_LOCATION,
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": STATICFILES_LOCATION,
                "file_overwrite": True,
            },
        }
    }

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="")
EMAIL_HOST = env.str("EMAIL_HOST", default="")
EMAIL_PORT = env.str("EMAIL_PORT", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")


'''

📝
🔗
🔑
📡
💾
💎
⌛️
⏰
🎄
🛡️
🥳
🥶
🍺
💡
🌋
👑
🚨
🔥
🌈
🎁
🎯
🎉
✨
🔎
🗑️
📐
✅
❌
🇺🇲
🇺🇿
💥
🍏
🍿
🌐
🚦
🚥
🚧
🛰️
🚀
🎈


'''
