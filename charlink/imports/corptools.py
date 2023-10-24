from django.db.models import Exists, OuterRef
from django.contrib.auth.models import User

from corptools.models import CharacterAudit
from corptools.tasks import update_character
from corptools.app_settings import get_character_scopes, CORPTOOLS_APP_NAME

from allianceauth.eveonline.models import EveCharacter
from allianceauth.authentication.models import CharacterOwnership

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)


def _is_character_added(character: EveCharacter):
    return CharacterAudit.objects.filter(character=character).exists()


def _users_with_perms():
    return User.objects.filter(
        Exists(CharacterOwnership.objects.filter(user_id=OuterRef('pk')))
    )


import_app = AppImport('corptools', [
    LoginImport(
        app_label='corptools',
        unique_id='default',
        field_label=CORPTOOLS_APP_NAME,
        add_character=_add_character,
        scopes=get_character_scopes(),
        check_permissions=lambda user: True,
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            CharacterAudit.objects
            .filter(character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
    # TODO corp audit
])
