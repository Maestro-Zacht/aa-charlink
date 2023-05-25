from django.db.models import Exists, OuterRef

from corptools.models import CharacterAudit
from corptools.tasks import update_character
from corptools.app_settings import get_character_scopes, CORPTOOLS_APP_NAME

from allianceauth.eveonline.models import EveCharacter

field_label = CORPTOOLS_APP_NAME

scopes = get_character_scopes()

permissions = []


def add_character(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)


def is_character_added(character: EveCharacter):
    return CharacterAudit.objects.filter(character=character).exists()


is_character_added_annotation = Exists(
    CharacterAudit.objects
    .filter(character_id=OuterRef('pk'))
)
