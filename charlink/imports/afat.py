from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission, User

from charlink.app_imports.utils import LoginImport, AppImport

from allianceauth.eveonline.models import EveCharacter

from app_utils.allianceauth import users_with_permission

from esi.models import Token

_scopes_readfleet = ["esi-fleets.read_fleet.v1"]
_scopes_clickfleet = ["esi-location.read_location.v1", "esi-location.read_ship_type.v1", "esi-location.read_online.v1"]


def _is_character_added_readfleet(character: EveCharacter):
    return (
        Token.objects
        .filter(character_id=character.character_id)
        .require_valid()
        .require_scopes(_scopes_readfleet)
        .exists()
    )


def _is_character_added_clickfleet(character: EveCharacter):
    return (
        Token.objects
        .filter(character_id=character.character_id)
        .require_valid()
        .require_scopes(_scopes_clickfleet)
        .exists()
    )


def _check_perms_readfleet(user: User):
    return user.has_perm('afat.manage_afat') or user.has_perm('afat.add_fatlink')


def _users_with_perms_readfleet():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='afat',
            codename='manage_afat'
        )
    ) | users_with_permission(
        Permission.objects.get(
            content_type__app_label='afat',
            codename='add_fatlink'
        )
    )


def _users_with_perms_clickfleet():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='afat',
            codename='basic_access'
        )
    )


app_import = AppImport('afat', [
    LoginImport(
        app_label='afat',
        unique_id='readfleet',
        field_label='AFAT Read Fleet',
        add_character=lambda token: None,
        scopes=_scopes_readfleet,
        check_permissions=_check_perms_readfleet,
        is_character_added=_is_character_added_readfleet,
        is_character_added_annotation=Exists(
            Token.objects.all()

            .filter(character_id=OuterRef('character_id'))
            .require_scopes(_scopes_readfleet)
            # .require_valid()
        ),
        get_users_with_perms=_users_with_perms_readfleet,
    ),
    LoginImport(
        app_label='afat',
        unique_id='clickfat',
        field_label='AFAT Click Fleet',
        add_character=lambda token: None,
        scopes=_scopes_clickfleet,
        check_permissions=lambda user: user.has_perm('afat.basic_access'),
        is_character_added=_is_character_added_clickfleet,
        is_character_added_annotation=Exists(
            Token.objects.all()
            .filter(character_id=OuterRef('character_id'))
            .require_scopes(_scopes_clickfleet)
            # .require_valid()
        ),
        get_users_with_perms=_users_with_perms_clickfleet,
    )
])
