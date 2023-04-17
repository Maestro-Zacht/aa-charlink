from importlib import import_module

from django.conf import settings

from allianceauth.services.hooks import get_extension_logger

logger = get_extension_logger(__name__)

_supported_apps = {}

_imported = False


def import_apps():
    global _imported
    if _imported:
        return _supported_apps

    for app in settings.INSTALLED_APPS:
        try:
            module = import_module(f'charlink.imports.{app}')
        except ModuleNotFoundError:
            pass
        else:
            _supported_apps[app] = {
                'field_label': module.field_label,
                'add_character': module.add_character,
            }

            logger.debug(f"Loading of {app} link: success")

    _imported = True
    return _supported_apps