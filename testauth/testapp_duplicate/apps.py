from django.apps import AppConfig


class TestAppDuplicateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testauth.testapp_duplicate'
