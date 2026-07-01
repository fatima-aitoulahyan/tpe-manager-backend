import os
from pathlib import Path
from decouple import config
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['localhost', '192.168.8.4', 'web']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',
    'rest_framework_simplejwt.token_blacklist',

    'apps.users',
    'apps.devis',
    'apps.billing',
    'apps.cashflow',
    'apps.credit',
    'apps.notifications',
    'apps.clients',

]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Casablanca'

USE_I18N = True

USE_TZ = True
CELERY_TIMEZONE = 'Africa/Casablanca'
CELERY_ENABLE_UTC = True


STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

SPECTACULAR_SETTINGS = {
    'TITLE': 'API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    'COMPONENT_SPLIT_REQUEST': True,

    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

FIREBASE_CREDENTIALS_PATH = BASE_DIR / 'config' / 'firebase-credentials.json'

CELERY_BROKER_URL = 'redis://redis:6379/0'

CELERY_BEAT_SCHEDULER = 'celery.beat:PersistentScheduler'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'rappel-factures-impayees': {
        'task': 'apps.notifications.tasks.rappel_factures_impayees',
        'schedule': crontab(hour=19, minute=5),
    },
    'rappel-devis-expirants': {
        'task': 'apps.notifications.tasks.rappel_devis_expirants',
        'schedule': crontab(hour=19, minute=5),
    },
    'rappel-declaration-fiscale': {
        'task': 'apps.notifications.tasks.rappel_declaration_fiscale',
        'schedule': crontab(hour=19, minute=5),
    },
    'rappel-cotisation-cnss': {
        'task': 'apps.notifications.tasks.rappel_cotisation_cnss',
        'schedule': crontab(hour=19, minute=5),
    },
}



TWILIO_ACCOUNT_SID  = config('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN   = config('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER')
TWILIO_MESSAGING_SERVICE_SID = config('TWILIO_MESSAGING_SERVICE_SID')

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True
