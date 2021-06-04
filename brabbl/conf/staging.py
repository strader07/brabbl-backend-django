from .base_public import *

MEDIA_ROOT = os.path.expanduser('~brabbl-staging/media')
STATIC_ROOT = os.path.expanduser('~brabbl-staging/static')

SESSION_COOKIE_SECURE = False
ALLOWED_HOSTS = ['staging.api.brabbl.com']
SITE_DOMAIN = 'staging.api.brabbl.com'
DATABASES['default']['NAME'] = 'brabbl-staging'
GUNICORN_PID_FILE = os.path.expanduser('~brabbl-staging/run/gunicorn.pid')

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

THEME_LOCATION_URL = 'http://staging.api.brabbl.com/embed/themes/'
