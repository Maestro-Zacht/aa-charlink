from corptools.models import CharacterAudit
from corptools.tasks import update_character

from allianceauth.eveonline.models import EveCharacter

field_label = 'Character Audit'


def add_character(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)
