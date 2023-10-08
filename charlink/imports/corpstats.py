from django.db.models import Exists, OuterRef

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from corpstats.models import CorpStat

from charlink.app_imports.utils import LoginImport, AppImport


def _add_character(request, token):
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


import_app = AppImport('corpstats', [
    LoginImport(
        app_label='corpstats',
        field_label='Corporation Stats',
        add_character=_add_character,
        scopes=[
            'esi-corporations.track_members.v1',
            'esi-universe.read_structures.v1'
        ],
        permissions=['corpstats.add_corpstat'],
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            CorpStat.objects
            .filter(token__character_id=OuterRef('character_id'))
        )
    ),
])
