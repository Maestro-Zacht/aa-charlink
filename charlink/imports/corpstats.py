from django.db.models import Exists, OuterRef

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from corpstats.models import CorpStat

field_label = 'Corporation Stats'

scopes = [
    'esi-corporations.track_members.v1',
    'esi-universe.read_structures.v1'
]

permissions = ['corpstats.add_corpstat']


def add_character(request, token):
    if EveCharacter.objects.filter(character_id=token.character_id).exists():
        corp_id = EveCharacter.objects.get(character_id=token.character_id).corporation_id
    else:
        corp_id = \
            token.get_esi_client().Character.get_characters_character_id(
                character_id=token.character_id).result()['corporation_id']
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
    except EveCorporationInfo.DoesNotExist:
        corp = EveCorporationInfo.objects.create_corporation(corp_id)
    cs = CorpStat.objects.create(token=token, corp=corp)
    cs.update()
    assert cs.pk  # ensure update was successful


def is_character_added(character: EveCharacter):
    return (
        CorpStat.objects
        .filter(token__character_id=character.character_id)
        .exists()
    )


is_character_added_annotation = Exists(
    CorpStat.objects
    .filter(token__character_id=OuterRef('character_id'))
)
