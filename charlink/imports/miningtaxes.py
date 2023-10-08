from django.db import transaction
from django.db.models import Exists, OuterRef

from miningtaxes.models import Character
from miningtaxes import tasks

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport


def _add_character(request, token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, _ = Character.objects.update_or_create(eve_character=eve_character)
    tasks.update_character.delay(character_pk=character.pk)


def _is_character_added(character: EveCharacter):
    return Character.objects.filter(eve_character=character).exists()


import_app = AppImport('miningtaxes', [
    LoginImport(
        field_label="Mining Taxes",
        add_character=_add_character,
        scopes=Character.get_esi_scopes(),
        permissions=["miningtaxes.basic_access"],
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            Character.objects
            .filter(eve_character_id=OuterRef('pk'))
        )
    ),
])
