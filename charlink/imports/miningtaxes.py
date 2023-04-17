from django.db import transaction

from miningtaxes.models import Character
from miningtaxes import tasks

from allianceauth.eveonline.models import EveCharacter

field_label = "Mining Taxes"

scopes = Character.get_esi_scopes()

permissions = ["miningtaxes.basic_access"]


def add_character(request, token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, _ = Character.objects.update_or_create(eve_character=eve_character)
    tasks.update_character.delay(character_pk=character.pk)
