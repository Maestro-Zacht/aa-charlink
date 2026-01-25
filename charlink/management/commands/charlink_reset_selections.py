from django.core.management.base import BaseCommand

from charlink.models import AppSettings
from charlink.app_imports import import_apps


class Command(BaseCommand):
    help = 'Reset login default selections'

    def handle(self, *args, **options):
        app_imports = import_apps()

        self.stdout.write('Resetting login options default selections...')

        for app_import in app_imports.values():
            for login_import in app_import.imports:
                AppSettings.objects.update_or_create(
                    app_name=login_import.get_query_id(),
                    defaults={
                        'default_selection': login_import.default_initial_selection,
                    }
                )

        self.stdout.write(self.style.SUCCESS('Reset done!'))
