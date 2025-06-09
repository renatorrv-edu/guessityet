import os
from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-this-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "drf_spectacular",
    "django_celery_beat",
    "bootstrap5",
    "guessityet",
]

SITE_ID = 1

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
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "guessityet_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Password validation
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
LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============= CONFIGURACIÓN DE APIS =============
# API Keys para servicios externos
RAWG_API_KEY = os.getenv("RAWG_API_KEY")
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============= CONFIGURACIÓN DE CELERY Y REDIS =============
# Usar las URLs de Redis del .env
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# También configurar la variable REDIS_URL para compatibilidad
REDIS_URL = CELERY_BROKER_URL

# Configuración moderna de Celery (compatible con 5.5.2)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Configuración para Celery Beat (tareas periódicas)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Configuración de tareas periódicas
CELERY_BEAT_SCHEDULE = {
    "select-daily-game": {
        "task": "guessityet.tasks.select_daily_game_igdb",
        "schedule": crontab(hour=23, minute=30),  # Ejecutar a las 23:30 cada día
        "options": {"expires": 60 * 60},  # Expira en 1 hora si no se ejecuta
    },
    "process-pending-gifs": {
        "task": "guessityet.tasks.batch_process_gifs",
        "schedule": crontab(hour=2, minute=0),  # Ejecutar a las 2:00 AM
        "kwargs": {"service_type": "igdb"},
        "options": {"expires": 60 * 60 * 2},  # Expira en 2 horas
    },
    "process-pending-screenshots": {
        "task": "guessityet.tasks.batch_process_screenshots_difficulty",
        "schedule": crontab(hour=3, minute=0),  # Ejecutar a las 3:00 AM
        "options": {"expires": 60 * 60 * 2},  # Expira en 2 horas
    },
}

# Configuración de timeouts y performance para Celery 5.5.2
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutos soft limit
CELERY_TASK_TIME_LIMIT = 600  # 10 minutos hard limit
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Configuración de conexión Redis con timeouts
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

# Configuración de resultados
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # Los resultados expiran en 24 horas
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {"retry_policy": {"timeout": 5.0}}

# Configuración de logging para Celery 5.5.2
CELERY_WORKER_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
CELERY_WORKER_TASK_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Configuración de seguridad
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_IGNORE_RESULT = False

# Configuración específica para tareas con video/imagen (moviepy, Pillow)
CELERY_TASK_ROUTES = {
    "guessityet.tasks.process_game_gif_async": {"queue": "media_processing"},
    "guessityet.tasks.batch_process_gifs": {"queue": "media_processing"},
    "guessityet.tasks.process_screenshots_difficulty": {"queue": "media_processing"},
}

# Colas específicas para diferentes tipos de tareas
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "media_processing": {
        "exchange": "media",
        "routing_key": "media.processing",
    },
}

# ============= CONFIGURACIÓN DE DJANGO REST FRAMEWORK =============
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ============= CONFIGURACIÓN DE SPECTACULAR (API DOCS) =============
SPECTACULAR_SETTINGS = {
    "TITLE": "GuessItYet API",
    "DESCRIPTION": "API para el juego de adivinanzas de videojuegos GuessItYet",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ============= CONFIGURACIÓN DE LOGGING =============
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
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "guessityet": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "celery": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Crear directorio de logs si no existe
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# ============= CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN =============
if not DEBUG:
    # Configuración de seguridad para producción
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Configurar hosts permitidos desde variable de entorno
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# ============= CONFIGURACIÓN DE SESIONES =============
# Configuración de sesiones para el juego
SESSION_COOKIE_AGE = 24 * 60 * 60  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============= CONFIGURACIÓN DE CACHE =============
# Usar Redis también para cache si está disponible
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "guessityet",
            "TIMEOUT": 300,  # 5 minutos por defecto
        }
    }
else:
    # Fallback a cache en memoria
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# ============= CONFIGURACIÓN DE EMAIL (opcional) =============
if os.getenv("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
else:
    # Fallback para desarrollo
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============= CONFIGURACIÓN ESPECÍFICA DEL JUEGO =============
# Configuración para el procesamiento de imágenes y videos
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]

# Configuración para IGDB y RAWG
GAME_CACHE_TIMEOUT = 60 * 60 * 24  # 24 horas
MAX_SCREENSHOTS_PER_GAME = 15
MAX_GAME_SEARCH_RESULTS = 25

# Configuración para el análisis de imágenes con IA
OPENAI_IMAGE_ANALYSIS_ENABLED = bool(OPENAI_API_KEY)
OPENAI_MAX_IMAGE_SIZE = 1024  # px
OPENAI_IMAGE_QUALITY = "low"  # Para reducir costos
