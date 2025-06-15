from config.settings import *

# Base de datos en memoria para tests rápidos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Desactivar migraciones complejas durante tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Configuración de testing
TESTING = True

# Desactivar logging durante tests para output más limpio
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "guessityet": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

# Usar templates simples para evitar errores de dependencias
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

# Desactivar cache durante tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Configuración de email simple para tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Password hashers más rápidos para tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Desactivar debug toolbar durante tests
if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS.remove("debug_toolbar")

# Middleware simplificado para tests
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Configuración estática simplificada
STATIC_URL = "/static/"
STATICFILES_DIRS = []

# Desactivar coleccionistas de archivos estáticos durante tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media simplificado
MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/test_media"

# Configuración de Celery para tests (ejecución síncrona)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# APIs de prueba (usar mocks)
RAWG_API_KEY = "test_rawg_key"
IGDB_CLIENT_ID = "test_igdb_client"
IGDB_CLIENT_SECRET = "test_igdb_secret"
OPENAI_API_KEY = "test_openai_key"

# Desactivar verificaciones SSL durante tests
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Secret key específica para tests
SECRET_KEY = "test-secret-key-not-for-production"
