from .base_public import *

MEDIA_ROOT = os.path.expanduser('~brabbl-staging/media')
STATIC_ROOT = os.path.expanduser('~brabbl-staging/static')

SESSION_COOKIE_SECURE = False
ALLOWED_HOSTS = ['staging.api.brabbl.com']
SITE_DOMAIN = 'staging.api.brabbl.com'
DATABASES['default']['NAME'] = 'brabbl-staging'
GUNICORN_PID_FILE = os.path.expanduser('~brabbl-staging/run/gunicorn.pid')

SOCIAL_AUTH_FACEBOOK_KEY = '517448505107678'
SOCIAL_AUTH_FACEBOOK_SECRET = 'ab56ee2ca70466e0ce24eb7cbaf83c52'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '1029460231592-pisjnovaqrodmbbeg7g6r9fcj8m9pfh7.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'sk3AN9Z1JGLamrVT75wkVJkP'

SOCIAL_AUTH_TWITTER_KEY = 'krescoig24pXrl770SEQHg3jC'
SOCIAL_AUTH_TWITTER_SECRET = 'chtCALsHS1OSSIKmWq7FlTMzQNKiD1GVl7fvWgkOynjnMjkDrQ'

THEME_LOCATION_URL = 'http://staging.api.brabbl.com/embed/themes/'
