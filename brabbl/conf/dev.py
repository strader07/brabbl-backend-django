from .base import *

DEBUG = True

SITE_DOMAIN = 'localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

STATICFILES_DIRS += (
    os.path.join(BASE_DIR, '..', 'frontend', 'dist'),
)

RQ_QUEUES = {
    'default': {
        'ASYNC': False,
    },
}

try:
    import django_extensions  # NOQA
except ImportError:
    pass
else:
    INSTALLED_APPS += ('django_extensions',)

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = (
    ''
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''


TIME_ZONE = 'Europe/Kiev'

THEME_LOCATION_URL = 'http://localhost:8080/dist/build/staging/themes/'

STATIC_ROOT = 'static_files'
