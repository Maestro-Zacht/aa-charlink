from dataclasses import dataclass
from typing import Callable

from django.http import HttpRequest
from django.db.models import Exists

from allianceauth.eveonline.models import EveCharacter
from esi.models import Token


@dataclass
class AppImport:
    field_label: str
    add_character: Callable[[HttpRequest, Token], None]
    scopes: list[str]
    permissions: list[str]
    is_character_added: Callable[[EveCharacter], bool]
    is_character_added_annotation: Exists
