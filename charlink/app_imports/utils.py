from dataclasses import dataclass
from typing import Callable

from django.http import HttpRequest
from django.db.models import Exists
from django import forms
from django.contrib.auth.models import User

from allianceauth.eveonline.models import EveCharacter
from esi.models import Token


@dataclass
class LoginImport:
    unique_id: str
    field_label: str
    add_character: Callable[[HttpRequest, Token], None]
    scopes: list[str]
    permissions: list[str]
    is_character_added: Callable[[EveCharacter], bool]
    is_character_added_annotation: Exists


@dataclass
class AppImport:
    app_label: str
    imports: list[LoginImport]

    def get_form_fields(self, user):
        return {
            f"{self.app_label}-{import_.unique_id}": forms.BooleanField(
                required=False,
                initial=True,
                label=import_.field_label
            )
            for import_ in self.imports
            if user.has_perms(import_.permissions)
        }

    def get_imports_with_perms(self, user: User):
        return AppImport(
            self.app_label,
            [
                import_
                for import_ in self.imports
                if user.has_perms(import_.permissions)
            ]
        )

    def has_any_perms(self, user: User):
        return any(user.has_perms(import_.permissions) for import_ in self.imports)
