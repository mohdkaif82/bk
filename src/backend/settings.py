"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import dj_database_url
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use Server as PRODUCTION or DEVELOPMENT
SERVER = config('SERVER',default='development')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY',default='9q$ntg=n=j*w1n9i3hya-5so*8@!nl1#-z#u-o6-46tp$7k6s$')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True #if SERVER == "DEVELOPMENT" else False

ALLOWED_HOSTS = ['*']

# Application definition

DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
)

LIBS = (
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'django_crontab',
    'django_query_signals',
    'mathfilters',
    'corsheaders',
    'django_rest_passwordreset',
    'pyfcm',
    'channels',
)

APPS = (
    'backend.accounts',
    'backend.base',
    'backend.practice',
    'backend.patients',
    'backend.billing',
    'backend.appointment',
    'backend.blog',
    'backend.inventory',
    'backend.mlm',
    'backend.doctors',
    'backend.meeting',
    'backend.muster_roll',
    'backend.mission_arogyam',
    'backend.android_user',
    'backend.mlm_compensation',
    'backend.chat',

    'backend.ecommers',
    
)

INSTALLED_APPS = DJANGO_APPS + LIBS + APPS

FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.TemporaryFileUploadHandler",)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'backend.middlewares.LogAllMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
   
]
STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
from django.utils.translation import gettext_lazy as _
ROOT_URLCONF = 'backend.urls'
LANGUAGES = [
      ('en',('English')),
      ('tr', ('Turkish')),
      ('hi',('Hindi')),
      ]

LANGUAGE_CODE = 'en-us'
LOCALE_PATHS = (
    os.path.join(BASE_DIR,"backend", 'locale'),
  )
DEFAULT_CHARSET = 'utf-8'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "backend", 'templates')],
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'libraries': {
                'calculate_age': 'backend.patients.templatetags.calculate_age'
            }
        }
    },
]

# WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'


#DATABASES = {'default': dj_database_url.config(default=config('DB_URabase_uL'))}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bk',
        'USER': 'ajay',
        'PASSWORD': 'Root@123',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_xml.renderers.XMLRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
}

CORS_ORIGIN_ALLOW_ALL = True

CORS_ORIGIN_WHITELIST = [
    'https://localhost:3000'
]

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "accounts.User"

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# STATIC_ROOT = os.path.join(BASE_DIR, 'backend', 'static')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR,"staticfiles")

# AWS Bucket Settings
if SERVER == "PRODUCTION":
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    DEFAULT_FILE_STORAGE = ''
    AWS_STORAGE_BUCKET_NAME =''
    AWS_S3_REGION_NAME = ''

    # Cron Jobs Settings
    CRONJOBS = [
        # ('0 2 * * *', 'backend.patients.crons.remind_appointment_today', '>> /tmp/appointment_reminder.log'),
        # ('30 6 * * *', 'backend.patients.crons.remind_appointment_tomorrow', '>> /tmp/appointment_reminder.log'),
        # ('30 1 * * *', 'backend.patients.crons.appointment_summary', '>> /tmp/scheduled_appointment_summary.log'),
        # ('30 1 * * *', 'backend.patients.crons.follow_up_and_medicine_reminder', '>> /tmp/follow_up_medicine.log'),
        # ('*/1 * * * *', 'backend.patients.crons.send_greetings', '>> /tmp/wish_sms.log'),
        # ('*/5 * * * *', 'backend.accounts.crons.update_referer', '>> /tmp/update_referer.log'),
        # ('*/1 * * * *', 'backend.patients.crons.send_greetings')
    ]
    
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ('rest_framework.renderers.JSONRenderer',)
CRONJOBS = [
        # ('0 2 * * *', 'backend.patients.crons.remind_appointment_today', '>> /tmp/appointment_reminder.log'),
        # ('30 6 * * *', 'backend.patients.crons.remind_appointment_tomorrow', '>> /tmp/appointment_reminder.log'),
        # ('30 1 * * *', 'backend.patients.crons.appointment_summary', '>> /tmp/scheduled_appointment_summary.log'),
        # ('*/1 * * * *', 'backend.patients.crons.follow_up_and_medicine_reminder', '>> /tmp/follow_up_medicine.log'),
        # ('*/1 * * * *', 'backend.patients.crons.send_greetings', '>> /tmp/wish_sms.log'),
        # ('*/5 * * * *', 'backend.accounts.crons.update_referer', '>> /tmp/update_referer.log'),
        ('*/5 * * * *', 'backend.patients.crons.call_reminder', '>> /tmp/call_reminder.log'),
    ]
# FCM Credentials
if SERVER == "PRODUCTION":
    DOMAIN = ''
    FCM_SERVER_KEY = ''
else:
    DOMAIN = ''
    FCM_SERVER_KEY = 'AIzaSyDvgRylz6_7NVfXNCBSCqvoXFruAgH53ZQ'

# Mailing Credentials
SMTP_USER = 'python.sartia@gmail.com'
SMTP_PASS = 'pgmmignlqptmblko'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = '587'

EMAIL_HOST = SMTP_HOST
DEFAULT_FROM_EMAIL = 'noreply@bkarogyam.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_HOST_USER = SMTP_USER
EMAIL_HOST_PASSWORD = SMTP_PASS
EMAIL_PORT = SMTP_PORT
EMAIL_USE_TLS = True

DEFAULT_EMAIL_FROM = SERVER_EMAIL

PASSWORD_RESET_URL = DOMAIN + "/password-reset/"
PASSWORD_SESSION_EXPIRE = 0

PASSWORD_RESET_TIME = 24 * 60 * 60

# Razorpay Credentials
RAZORPAY_ID ='rzp_test_48Z9LMTDVAN5JU'
RAZORPAY_SECRET = 'gMxfhwgZ73ANYJQCeblLMy7W'




FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
# Logger Settings
import logging.config

LOGGING_CONFIG = None

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        # Add Handler for Slack for warning and above
        'slack': {
            'level': 'ERROR',
            'class': 'backend.slack_logger.SlackExceptionHandler',
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console', 'slack'],
        },
        'app_name': {
            'level': 'INFO',
            'handlers': ['console', 'slack'],
            # required to avoid double logging with root logger
            'propagate': False,
        },
    },
})
import redis
REDIS_DEFAULT_CONNECTION_POOL = redis.ConnectionPool.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/'))

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

