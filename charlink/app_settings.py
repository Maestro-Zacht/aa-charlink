from django.conf import settings

CHARLINK_IGNORE_APPS = set(getattr(settings, 'CHARLINK_IGNORE_APPS', []))
