from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.corputils.models import CorpStats

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character(token):
    corp_id = EveCharacter.objects.get(character_id=token.character_id).corporation_id
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
    except EveCorporationInfo.DoesNotExist:
        corp = EveCorporationInfo.objects.create_corporation(corp_id)
    cs = CorpStats.objects.create(token=token, corp=corp)
    cs.update()
    assert cs.pk  # ensure update was successful


def _is_character_added(character: EveCharacter):
    return (
        CorpStats.objects
        .filter(token__character_id=character.character_id)
        .exists()
    )


def _users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='corputils',
            codename='add_corpstats'
        )
    )


app_import = AppImport('allianceauth.corputils', [
    LoginImport(
        app_label='allianceauth.corputils',
        unique_id='default',
        field_label='Corporation Stats',
        add_character=_add_character,
        scopes=['esi-corporations.read_corporation_membership.v1'],
        check_permissions=lambda user: user.has_perm('corputils.add_corpstats'),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            CorpStats.objects
            .filter(token__character_id=OuterRef('character_id'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
])
