from django.db import transaction
from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from miningtaxes.models import Character
from miningtaxes import tasks

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character(token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, _ = Character.objects.update_or_create(eve_character=eve_character)
    tasks.update_character.delay(character_pk=character.pk)


def _is_character_added(character: EveCharacter):
    return Character.objects.filter(eve_character=character).exists()


def _users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='miningtaxes',
            codename='basic_access'
        )
    )


app_import = AppImport('miningtaxes', [
    LoginImport(
        app_label='miningtaxes',
        unique_id='default',
        field_label="Mining Taxes",
        add_character=_add_character,
        scopes=Character.get_esi_scopes(),
        check_permissions=lambda user: user.has_perm("miningtaxes.basic_access"),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            Character.objects
            .filter(eve_character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
])
