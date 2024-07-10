from django.contrib.auth.models import Permission
from django.contrib import messages
from django.db.models import Exists, OuterRef

from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter, EveCorporationInfo

from aa_contacts.models import AllianceToken, CorporationToken
from aa_contacts.tasks import update_alliance_contacts, update_corporation_contacts

from esi.models import Token

from app_utils.allianceauth import users_with_permission

from ..app_imports.utils import LoginImport, AppImport

ALLIANCE_SCOPES = ['esi-alliances.read_contacts.v1']
CORPORATION_SCOPES = ['esi-corporations.read_contacts.v1']


def _alliance_login(request, token: Token):
    char = EveCharacter.objects.get(character_id=token.character_id)

    if char.alliance_id is None:
        messages.error(request, 'Character is not in an alliance')
        assert False

    try:
        alliance = char.alliance
    except EveAllianceInfo.DoesNotExist:
        alliance = EveAllianceInfo.objects.create_alliance(char.alliance_id)

    if AllianceToken.objects.filter(alliance=alliance).exists():
        messages.error(request, f'{alliance} already has a token')
        assert False

    AllianceToken.objects.create(alliance=alliance, token=token)
    update_alliance_contacts.delay(alliance.alliance_id)


def _corporation_login(request, token: Token):
    char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        corporation = char.corporation
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(char.corporation_id)

    if CorporationToken.objects.filter(corporation=corporation).exists():
        messages.error(request, f'{corporation} already has a token')
        assert False

    CorporationToken.objects.create(corporation=corporation, token=token)
    update_corporation_contacts.delay(corporation.corporation_id)


def _alliance_users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='aa_contacts',
            codename='manage_alliance_contacts'
        )
    )


def _corporation_users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='aa_contacts',
            codename='manage_corporation_contacts'
        )
    )


def _alliance_check_perms(user):
    return user.has_perm('aa_contacts.manage_alliance_contacts')


def _corporation_check_perms(user):
    return user.has_perm('aa_contacts.manage_corporation_contacts')


def _alliance_is_character_added(char: EveCharacter):
    return AllianceToken.objects.filter(token__character_id=char.character_id).exists()


def _corporation_is_character_added(char: EveCharacter):
    return CorporationToken.objects.filter(token__character_id=char.character_id).exists()


app_import = AppImport(
    "aa_contacts",
    [
        LoginImport(
            app_label="aa_contacts",
            unique_id="alliance",
            field_label="Alliance Contacts",
            add_character=_alliance_login,
            scopes=ALLIANCE_SCOPES,
            check_permissions=_alliance_check_perms,
            is_character_added=_alliance_is_character_added,
            is_character_added_annotation=Exists(
                AllianceToken.objects.filter(
                    token__character_id=OuterRef('character_id'),
                )
            ),
            get_users_with_perms=_alliance_users_with_perms
        ),
        LoginImport(
            app_label="aa_contacts",
            unique_id="corporation",
            field_label="Corporation Contacts",
            add_character=_corporation_login,
            scopes=CORPORATION_SCOPES,
            check_permissions=_corporation_check_perms,
            is_character_added=_corporation_is_character_added,
            is_character_added_annotation=Exists(
                CorporationToken.objects.filter(
                    token__character_id=OuterRef('character_id'),
                )
            ),
            get_users_with_perms=_corporation_users_with_perms
        )
    ]
)
