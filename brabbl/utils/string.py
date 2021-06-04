import random
import string

from django.conf import settings


def random_string(size=32, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for __ in range(size))


def add_widget_hashtag(url):
    """Delete existing hashtag, and add widget's hashtag"""
    return url.split("#")[0] + settings.WIDGET_HASHTAG
