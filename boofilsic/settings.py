"""
Django settings for boofilsic project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import psycopg2.extensions

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'nbv58c^&b8-095(^)&_BV98596v)&CX#^$&%*^V5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# To allow debug in template context
# https://docs.djangoproject.com/en/3.1/ref/settings/#internal-ips
INTERNAL_IPS = [
    "127.0.0.1"
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.postgres',
    'markdownx',
    'management.apps.ManagementConfig',
    'mastodon.apps.MastodonConfig',
    'common.apps.CommonConfig',
    'users.apps.UsersConfig',
    'books.apps.BooksConfig',
    'movies.apps.MoviesConfig',
    'music.apps.MusicConfig',
    'games.apps.GamesConfig',
    'easy_thumbnails',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'boofilsic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'boofilsic.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test',
            'USER': 'donotban',
            'PASSWORD': 'donotbansilvousplait',
            'HOST': '172.18.116.29',
            'OPTIONS': {
                'client_encoding': 'UTF8',
                # 'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_DEFAULT,
            }
        }    
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'boofilsic',
            'USER': 'doubaniux',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'OPTIONS': {
                'client_encoding': 'UTF8',
                # 'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_DEFAULT,
            }
        }    
    }

# Customized auth backend, glue OAuth2 and Django User model together
# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#authentication-backends

AUTHENTICATION_BACKENDS = [
    'mastodon.auth.OAuth2Backend',
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '{levelname} {asctime} {name}:{lineno} {message}',
                'style': '{',
            },
        },    
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': os.path.join(BASE_DIR, 'log'),
                'formatter': 'simple'
            },
        },
        'root': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    }

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

AUTH_USER_MODEL = 'users.User'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Mastodon configs
CLIENT_NAME = 'NiceDB'
APP_WEBSITE = 'https://nicedb.org'
REDIRECT_URIS = "https://nicedb.org/users/OAuth2_login/\nhttps://www.nicedb.org/users/OAuth2_login/"

# Path to save report related images, ends with slash
REPORT_MEDIA_PATH_ROOT = 'report/'
MARKDOWNX_MEDIA_PATH = 'review/'
BOOK_MEDIA_PATH_ROOT = 'book/'
DEFAULT_BOOK_IMAGE = os.path.join(BOOK_MEDIA_PATH_ROOT, 'default.svg')
MOVIE_MEDIA_PATH_ROOT = 'movie/'
DEFAULT_MOVIE_IMAGE = os.path.join(MOVIE_MEDIA_PATH_ROOT, 'default.svg')
SONG_MEDIA_PATH_ROOT = 'song/'
DEFAULT_SONG_IMAGE = os.path.join(SONG_MEDIA_PATH_ROOT, 'default.svg')
ALBUM_MEDIA_PATH_ROOT = 'album/'
DEFAULT_ALBUM_IMAGE = os.path.join(ALBUM_MEDIA_PATH_ROOT, 'default.svg')
GAME_MEDIA_PATH_ROOT = 'game/'
DEFAULT_GAME_IMAGE = os.path.join(GAME_MEDIA_PATH_ROOT, 'default.svg')

# Timeout of requests to Mastodon, in seconds
MASTODON_TIMEOUT = 30

# Tags for toots posted from this site
MASTODON_TAGS = '#NiceDB #NiceDB%(category)s #NiceDB%(category)s%(type)s'

# Emoji code in mastodon
STAR_SOLID = ':star_solid:'
STAR_HALF = ':star_half:'
STAR_EMPTY = ':star_empty:'

# Default password for each user. since assword is not used any way,
# any string that is not empty is ok
DEFAULT_PASSWORD = 'ab7nsm8didusbaqPgq'

# Default redirect loaction when access login required view
LOGIN_URL = '/users/login/'

# Admin site root url
ADMIN_URL = 'tertqX7256n7ej8nbv5cwvsegdse6w7ne5rHd'

# Luminati proxy settings
LUMINATI_USERNAME = 'lum-customer-hl_nw4tbv78-zone-static'
LUMINATI_PASSWORD = 'nsb7te9bw0ney'

# ScraperAPI api key
SCRAPERAPI_KEY = 'wnb3794v675b8w475h0e8hr7tyge'

# Spotify credentials
SPOTIFY_CREDENTIAL = "NzYzNkYTE6MGQ0ODY0NTY2Y2b3n645sdfgAyY2I1ljYjg3Nzc0MjIwODQ0ZWE="

# IMDb API service https://imdb-api.com/
IMDB_API_KEY = "k23fwewff23"

# Thumbnail setting
# It is possible to optimize the image size even more: https://easy-thumbnails.readthedocs.io/en/latest/ref/optimize/
THUMBNAIL_ALIASES = {
    '': {
        'normal': {
            'size': (200, 200),
            'crop': 'scale',
            'autocrop': True,
        },
    },
}
# THUMBNAIL_PRESERVE_EXTENSIONS = ('svg',)
if DEBUG:
    THUMBNAIL_DEBUG = True

# https://django-debug-toolbar.readthedocs.io/en/latest/
# maybe benchmarking before deployment
