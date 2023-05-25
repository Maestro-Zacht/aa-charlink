from django.db.models import Exists, OuterRef

from moonstuff.providers import ESI_CHARACTER_SCOPES
from moonstuff.models import TrackingCharacter
from moonstuff.tasks import import_extraction_data

from allianceauth.eveonline.models import EveCharacter

field_label = 'Moon Tools'

scopes = ESI_CHARACTER_SCOPES

permissions = ['moonstuff.add_trackingcharacter']


def add_character(request, token):
    eve_char = EveCharacter.objects.get(character_id=token.character_id)

    if not TrackingCharacter.objects.filter(character=eve_char).exists():
        char = TrackingCharacter(character=eve_char)
        char.save()

        # Schedule an import task to pull data from the new Tracking Character.
        import_extraction_data.delay()


def is_character_added(character: EveCharacter):
    return TrackingCharacter.objects.filter(character=character).exists()


is_character_added_annotation = Exists(
    TrackingCharacter.objects
    .filter(character_id=OuterRef('pk'))
)
