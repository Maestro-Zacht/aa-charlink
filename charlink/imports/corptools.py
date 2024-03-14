from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission, User

from corptools.models import CharacterAudit, CorporationAudit
from corptools.tasks import update_character, update_all_corps
from corptools.app_settings import get_character_scopes, CORPTOOLS_APP_NAME
from corptools.views import CORP_REQUIRED_SCOPES

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission

_corp_perms = [
    'corptools.own_corp_manager',
    'corptools.alliance_corp_manager',
    'corptools.state_corp_manager',
    'corptools.global_corp_manager',
    'corptools.holding_corp_structures',
    'corptools.holding_corp_assets',
    'corptools.holding_corp_wallets'
]


def _add_character_charaudit(token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)


def _add_character_corp(token):
    char = EveCharacter.objects.get_character_by_id(token.character_id)
    corp, created = EveCorporationInfo.objects.get_or_create(corporation_id=char.corporation_id,
                                                             defaults={'member_count': 0,
                                                                       'corporation_ticker': char.corporation_ticker,
                                                                       'corporation_name': char.corporation_name
                                                                       })
    CorporationAudit.objects.update_or_create(corporation=corp)
    update_all_corps.apply_async(priority=6)


def _check_perms_corp(user: User):
    return any(user.has_perm(perm) for perm in _corp_perms)


def _is_character_added_charaudit(character: EveCharacter):
    return CharacterAudit.objects.filter(character=character).exists()


def _is_character_added_corp(character: EveCharacter):
    return CorporationAudit.objects.filter(corporation__corporation_id=character.corporation_id).exists()


def _users_with_perms_charaudit():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='corptools',
            codename='view_characteraudit'
        )
    )


def _users_with_perms_corp():
    users = users_with_permission(
        Permission.objects.get(
            content_type__app_label=_corp_perms[0].split('.')[0],
            codename=_corp_perms[0].split('.')[1]
        )
    )
    for perm_str in _corp_perms[1:]:
        users |= users_with_permission(
            Permission.objects.get(
                content_type__app_label=perm_str.split('.')[0],
                codename=perm_str.split('.')[1]
            )
        )

    return users


app_import = AppImport('corptools', [
    LoginImport(
        app_label='corptools',
        unique_id='default',
        field_label=CORPTOOLS_APP_NAME,
        add_character=_add_character_charaudit,
        scopes=get_character_scopes(),
        check_permissions=lambda user: user.has_perm('corptools.view_characteraudit'),
        is_character_added=_is_character_added_charaudit,
        is_character_added_annotation=Exists(
            CharacterAudit.objects
            .filter(character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms_charaudit,
    ),
    LoginImport(
        app_label='corptools',
        unique_id='structures',
        field_label="Corporation Audit",
        add_character=_add_character_corp,
        scopes=CORP_REQUIRED_SCOPES,
        check_permissions=_check_perms_corp,
        is_character_added=_is_character_added_corp,
        is_character_added_annotation=Exists(
            CorporationAudit.objects
            .filter(corporation__corporation_id=OuterRef('corporation_id'))
        ),
        get_users_with_perms=_users_with_perms_corp,
    )
])
