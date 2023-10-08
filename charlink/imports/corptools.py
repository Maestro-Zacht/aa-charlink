from django.db.models import Exists, OuterRef

from corptools.models import CharacterAudit
from corptools.tasks import update_character
from corptools.app_settings import get_character_scopes, CORPTOOLS_APP_NAME

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport


def _add_character(request, token):
    CharacterAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id))
    update_character.apply_async(args=[token.character_id], priority=6)


def _is_character_added(character: EveCharacter):
    return CharacterAudit.objects.filter(character=character).exists()


import_app = AppImport('corptools', [
    LoginImport(
        field_label=CORPTOOLS_APP_NAME,
        add_character=_add_character,
        scopes=get_character_scopes(),
        permissions=[],
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            CharacterAudit.objects
            .filter(character_id=OuterRef('pk'))
        )
    ),
    # TODO corp audit
])
