from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from corpstats.models import CorpStat

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character(token):
    corp_id = EveCharacter.objects.get(character_id=token.character_id).corporation_id
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
    except EveCorporationInfo.DoesNotExist:
        corp = EveCorporationInfo.objects.create_corporation(corp_id)
    cs = CorpStat.objects.create(token=token, corp=corp)
    cs.update()
    assert cs.pk  # ensure update was successful


def _is_character_added(character: EveCharacter):
    return (
        CorpStat.objects
        .filter(token__character_id=character.character_id)
        .exists()
    )


def _users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='corpstats',
            codename='add_corpstat'
        )
    )


app_import = AppImport('corpstats', [
    LoginImport(
        app_label='corpstats',
        unique_id='default',
        field_label='Corporation Stats',
        add_character=_add_character,
        scopes=[
            'esi-corporations.track_members.v1',
            'esi-universe.read_structures.v1'
        ],
        check_permissions=lambda user: user.has_perm('corpstats.add_corpstat'),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            CorpStat.objects
            .filter(token__character_id=OuterRef('character_id'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
])
