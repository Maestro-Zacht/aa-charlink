from corptools.models import CharacterAudit
from corptools.tasks import update_character
from corptools.app_settings import get_character_scopes

from allianceauth.eveonline.models import EveCharacter

field_label = 'Character Audit'

scopes = get_character_scopes()

permissions = []


def add_character(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)
