###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## planta project settings.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================

import sys

# =====================
# project import
# =====================

from helpers import filesystem as h_fs


# add apps root to sys.path
sys.path.append(h_fs.get_absolute_path('../apps', __file__))

PROJECT_ROOT = h_fs.get_abs_path(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = False

ADMINS = (
    ('Pedro Barbosa', 'palb@cacr.caltech.edu'),
    )

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'planta',
        'USER': 'planta',
        'PASSWORD': '123',
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB;',
            'unix_socket': '/var/run/mysqld/mysqld.sock'
        }
    },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': './db/data.db',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = h_fs.get_absolute_path('../media/', __file__)
if DEBUG:
    MEDIA_ROOT = h_fs.get_absolute_path('../media/', __file__)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = h_fs.get_absolute_path('../../static/', __file__)

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    ('common', h_fs.get_absolute_path('../static/common', __file__)),
    ('crowd/tileui', h_fs.get_absolute_path('../static/crowd/tileui',
        __file__)),
    ('crowd/workers', h_fs.get_absolute_path('../static/crowd/workers',
        __file__)),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
    )

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@1sjo*%ynn$t&amp;%%pt(9o6as+mln63xd1oq-paxpp3(oloy5ks1'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware'
    )

ROOT_URLCONF = 'planta.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'planta.wsgi.application'

TEMPLATE_DIRS = (h_fs.get_absolute_path('../templates', __file__),)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',

    # external apps
    'registration',
    'django_extensions',
    'widget_tweaks',
    #'debug_toolbar',
    'south',

    # project apps
    'apps.profiles',
    'apps.crowd',
    )

# ===========================
# logging stuff configuration
# ===========================

def require_debug_true_callback_filter(r):
    from django.conf import settings


    return settings.DEBUG


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': '%(levelname)s:%(asctime)s:%(pathname)s:%(lineno)d -> '
                      '%(message)s'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': require_debug_true_callback_filter
        }
    },
    'handlers': {
        'debug': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'normal'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True  # WARNING this can be potentially unsafe
        }
    },
    'loggers': {
        'debug': {
            'handlers': ['debug'],
            'level': 'DEBUG'
        },
        'internal_errors': {
            'handlers': ['mail_admins', 'debug'],
            'level': 'ERROR'
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True
        }
    }
}

# ==========================
# e-mail stuff configuration
# ==========================

SERVER_EMAIL = 'cunha@cacr.caltech.edu'
DEFAULT_FROM_EMAIL = SERVER_EMAIL
EMAIL_HOST = 'smtp.cacr.caltech.edu'
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_PORT = 25
#EMAIL_USE_TLS = True

# ========================================
# registration and auth apps configuration
# ========================================

AUTH_PROFILE_MODULE = 'profiles.UserProfile'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'
ACCOUNT_ACTIVATION_DAYS = 2

# ===========================
# testing stuff configuration
# ===========================

FIXTURE_DIRS = (h_fs.get_absolute_path('../db/fixtures', __file__),)
TEST_RUNNER = 'planta.test_runner.TestRunner'

# ===========================
# miscellaneous configuration
# ===========================

INTERNAL_IPS = ('127.0.0.1',)

# ===========================
# Cache configuration
# ===========================
CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# ===========================
# Celery configuration
# ===========================
BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 100}
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
