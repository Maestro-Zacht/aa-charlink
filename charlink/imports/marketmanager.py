from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport

from marketmanager.views import CHARACTER_SCOPES, CORPORATION_SCOPES
from app_utils.allianceauth import users_with_permission
from esi.models import Token


def _is_character_added_character_login(character: EveCharacter):
    return (
        Token.objects
        .filter(character_id=character.character_id)
        .require_valid()
        .require_scopes(CHARACTER_SCOPES)
        .exists()
    )


def _is_character_added_corporation_login(character: EveCharacter):
    return (
        Token.objects
        .filter(character_id=character.character_id)
        .require_valid()
        .require_scopes(CORPORATION_SCOPES)
        .exists()
    )


app_import = AppImport('marketmanager', [
    LoginImport(
        app_label='marketmanager',
        unique_id='character',
        field_label='Market Manager Character Login',
        add_character=lambda token: None,
        scopes=CHARACTER_SCOPES,
        check_permissions=lambda user: user.has_perm("marketmanager.basic_market_browser"),
        is_character_added=_is_character_added_character_login,
        is_character_added_annotation=Exists(
            Token.objects
            .filter(character_id=OuterRef('character_id'))
            .require_scopes(CHARACTER_SCOPES)
        ),
        get_users_with_perms=lambda: users_with_permission(Permission.objects.get(content_type__app_label='marketmanager', codename='basic_market_browser'))
    ),
    LoginImport(
        app_label='marketmanager',
        unique_id='corporation',
        field_label='Market Manager Corporation Login',
        add_character=lambda token: None,
        scopes=CORPORATION_SCOPES,
        check_permissions=lambda user: user.has_perm("marketmanager.basic_market_browser"),
        is_character_added=_is_character_added_corporation_login,
        is_character_added_annotation=Exists(
            Token.objects
            .filter(character_id=OuterRef('character_id'))
            .require_scopes(CORPORATION_SCOPES)
        ),
        get_users_with_perms=lambda: users_with_permission(Permission.objects.get(content_type__app_label='marketmanager', codename='basic_market_browser'))
    )
])
