# keys, apis, and other stuff that mmda uses

LASTFM_API_KEY = '' # key that is used with last.fm database queries
                                                    # if you use this software please replace it with your own key(!)
                                                    # it can be obtained for free at http://www.last.fm/api/account

FLICKR_API_KEY = '' # flickr key
                                                    # if you use this software please replace it with your own key(!)
                                                    # it can be obtained for free at http://www.flickr.com/services/api

#MB_WEBSERVICE_HOST  = 'musicbrainz.org'             # mmda is efficient, but with many concurrent users it can
MB_WEBSERVICE_HOST  = 'www.uk.musicbrainz.org'             # mmda is efficient, but with many concurrent users it can
#MB_WEBSERVICE_HOST  = 'music.aergia.eu'             # mmda is efficient, but with many concurrent users it can
                                                    # make more than 1 req/s, so it should use mirror server
                                                    # when deployed


USER_AGENT = "MMDA/0.1 +http://music.aergia.eu/"    # how MMDA should say hello to other servers ;-)

# Django settings for mmda project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('Marcin Rataj', 'm@lidel.org'),
)

MANAGERS = ADMINS

COUCHDB_DATABASES = (
    ('mmda.artists', 'http://127.0.0.1:5984/mmda-artists'),
    ('mmda.pictures', 'http://127.0.0.1:5984/mmda-pictures'),
    ('mmda.videos', 'http://127.0.0.1:5984/mmda-videos'),
    ('mmda.tags', 'http://127.0.0.1:5984/mmda-tags'),
    ('mmda.news', 'http://127.0.0.1:5984/mmda-news'),
    ('mmda.search', 'http://127.0.0.1:5984/mmda-search'),
)

DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'mmda'         # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Warsaw'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%@x3!4ucuz%ifi-o8e1+g=-^jq+0ux40(3k39dle)k9h6$tp=2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'mmda.urls'

TEMPLATE_DIRS = (
    '/home/lidel/work/magisterka/django_app/mmda/templates',
)

INSTALLED_APPS = (
    'couchdbkit.ext.django',
    'mmda.artists',
    'mmda.tags',
    'mmda.news',
    'mmda.pictures',
    'mmda.videos',
    'mmda.search',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.sites',
)
