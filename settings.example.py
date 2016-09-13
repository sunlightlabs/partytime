# Django settings for partytime project.
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('panic', 'panic@sunlightfoundation.com'),
    ('name', 'test@example.com')
)

MANAGERS = ADMINS

INTERNAL_IPS = ('127.0.0.1')

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
USE_I18N = True

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'partytime',
        'USER': 'partytime',
        'PASSWORD': 'mysecretpassword',
        'HOST': 'localhost',
        'PORT': '',
    }
}
DATABASES['wordpress'] = DATABASES['default']

MEDIA_URL = 'http://widgets.politicalpartytime.org' # Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_ROOT = '' # Example: "/home/media/media.lawrence.com/"

#STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
#print "STATIC ROOT IS: %s" % STATIC_ROOT
STATIC_URL = 'http://assets.politicalpartytime.org/1.0/'

STATICFILES_DIRS = (
  os.path.join(PROJECT_ROOT, 'static/'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)



ADMIN_MEDIA_PREFIX = 'http://assets.sunlightfoundation.com/admin/1.3/'

SECRET_KEY = 'its a secret to everybody'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.app_directories.Loader'
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'publicsite.context_processors.get_current_url',
    'publicsite.context_processors.get_current_url_with_querystring',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'locksmith.auth.middleware.APIKeyMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'partytime.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'contact_form',
    'mediasync',
    'wordpress',
    'publicsite',
    'debug_toolbar',
    'gunicorn',
    'tastypie',
    'locksmith.auth',
    'api',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# new email settings
EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'
POSTMARK_API_KEY = 'postmark-key'
POSTMARK_SENDER = 'partytime@sunlightfoundation.com'

# for API
API_LIMIT_PER_PAGE = 100
AWS_ACCESS_KEY_ID = "aws access key"
AWS_SECRET_ACCESS_KEY = "aws secret key"
AWS_BUCKET = "widgets.politicalpartytime.org"


MEDIASYNC = {
    'BACKEND': 'mediasync.backends.s3',
    'AWS_KEY': AWS_ACCESS_KEY_ID,
    'AWS_SECRET': AWS_SECRET_ACCESS_KEY,
    'AWS_BUCKET': 'assets.sunlightfoundation.com',
    'AWS_PREFIX': 'partytime/3.0',
    'AWS_BUCKET_CNAME': True,
    'DOCTYPE': 'html5',
    'PROCESSORS': (
        'mediasync.processors.closurecompiler.compile',
        'mediasync.processors.slim.css_minifier',
    ),
    'JOINED': {
        'css/partytime.css': (
            'css/blueprint.css',
            'css/style.css',
        ),
    },
    # 'CACHE_BUSTER': 201105131223,
}


SCRIBD_KEY = 'scribd key'
SCRIBD_SECRET = 'scribd secret'

try:
    from local_settings import *
except ImportError, exp:
    pass
