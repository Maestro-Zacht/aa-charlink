from django.db.models import Exists, OuterRef

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.corputils.models import CorpStats

field_label = 'Corporation Stats'

scopes = ['esi-corporations.read_corporation_membership.v1']

permissions = ['corputils.add_corpstats']


def add_character(request, token):
    corp_id = EveCharacter.objects.get(character_id=token.character_id).corporation_id
    try:
        corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
    except EveCorporationInfo.DoesNotExist:
        corp = EveCorporationInfo.objects.create_corporation(corp_id)
    cs = CorpStats.objects.create(token=token, corp=corp)
    cs.update()
    assert cs.pk  # ensure update was successful


def is_character_added(character: EveCharacter):
    return (
        CorpStats.objects
        .filter(token__character_id=character.character_id)
        .exists()
    )


is_character_added_annotation = Exists(
    CorpStats.objects
    .filter(token__character_id=OuterRef('character_id'))
)
