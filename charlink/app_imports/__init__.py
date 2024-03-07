from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef

from allianceauth.services.hooks import get_extension_logger
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.hooks import get_hooks

from .utils import LoginImport, AppImport

logger = get_extension_logger(__name__)

_supported_apps = {
    'add_character': AppImport('add_character', [
        LoginImport(
            app_label='add_character',
            unique_id='default',
            field_label='Add Character (default)',
            add_character=lambda request, token: None,
            scopes=['publicData'],
            check_permissions=lambda user: True,
            is_character_added=lambda character: CharacterOwnership.objects.filter(character=character).exists(),
            is_character_added_annotation=Exists(CharacterOwnership.objects.filter(character_id=OuterRef('pk'))),
            get_users_with_perms=lambda: User.objects.filter(
                Exists(CharacterOwnership.objects.filter(user_id=OuterRef('pk')))
            ),
        )
    ])
}

_imported = False


def import_apps():
    global _imported
    if not _imported:
        # hooks
        charlink_hooks = get_hooks('charlink')

        for hook_f in charlink_hooks:
            hook_mod = hook_f()
            try:
                assert isinstance(hook_mod, str)
                app_import: AppImport = import_module(hook_mod).app_import
                AppImport.validate_import(app_import)
            except AssertionError:
                logger.debug(f"Loading of {hook_mod} link via hook: failed to validate")
            except ModuleNotFoundError:
                logger.debug(f"Loading of {hook_mod} link via hook: failed to import")
            except:
                logger.debug(f"Loading of {hook_mod} link via hook: failed")
            else:
                _supported_apps[app_import.app_label] = app_import
                logger.debug(f"Loading of {hook_mod} link via hook: success")

        # defaults
        for app in settings.INSTALLED_APPS:
            if app != 'allianceauth' and app not in _supported_apps:
                try:
                    module = import_module(f'charlink.imports.{app}')
                except ModuleNotFoundError:
                    logger.debug(f"Loading of {app} link: failed")
                else:
                    _supported_apps[app] = module.app_import
                    logger.debug(f"Loading of {app} link: success")

        _imported = True

    return _supported_apps
