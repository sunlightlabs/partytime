
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

FILE_UPLOAD_PATH = "/dev/null" # no trailing slash

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
DATABASES['wordpress'] = DATABASES['default']

STATIC_URL = "/static/"

CACHE_TIME_MINUTES = 15

API_LIMIT_PER_PAGE = 50
LOCKSMITH_HUB_URL = ''
LOCKSMITH_SIGNING_KEY = ''
LOCKSMITH_API_NAME = 'politicalpartytime'
