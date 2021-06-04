from .base_public import *


SITE_DOMAIN = 'api.brabbl.com'

ALLOWED_HOSTS = ['api.brabbl.com']

SESSION_COOKIE_SECURE = True

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = ''
MAILGUN_SERVER_NAME = 'brabbl.com'
GUNICORN_PID_FILE = os.path.expanduser('~brabbl/run/gunicorn.pid')

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

THEME_LOCATION_URL = 'https://api.brabbl.com/embed/themes/'
