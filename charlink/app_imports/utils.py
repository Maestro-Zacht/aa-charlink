from dataclasses import dataclass
from typing import Callable, List

from django.http import HttpRequest
from django.db.models import Exists, QuerySet
from django import forms
from django.contrib.auth.models import User

from allianceauth.eveonline.models import EveCharacter
from esi.models import Token


@dataclass
class LoginImport:
    app_label: str
    unique_id: str
    field_label: str
    add_character: Callable[[HttpRequest, Token], None]
    scopes: List[str]
    check_permissions: Callable[[User], bool]
    is_character_added: Callable[[EveCharacter], bool]
    is_character_added_annotation: Exists
    get_users_with_perms: Callable[[], QuerySet[User]]

    def get_query_id(self):
        return f"{self.app_label}_{self.unique_id}"

    def __hash__(self) -> int:
        return hash(self.get_query_id())

    @staticmethod
    def validate_import(login_import: 'LoginImport'):
        assert hasattr(login_import, 'app_label')
        assert hasattr(login_import, 'unique_id')
        assert hasattr(login_import, 'field_label')
        assert hasattr(login_import, 'add_character')
        assert hasattr(login_import, 'scopes')
        assert hasattr(login_import, 'check_permissions')
        assert hasattr(login_import, 'is_character_added')
        assert hasattr(login_import, 'is_character_added_annotation')
        assert hasattr(login_import, 'get_users_with_perms')
        assert isinstance(login_import.app_label, str)
        assert isinstance(login_import.unique_id, str)
        assert isinstance(login_import.field_label, str)
        assert callable(login_import.add_character)
        assert isinstance(login_import.scopes, list)
        assert callable(login_import.check_permissions)
        assert callable(login_import.is_character_added)
        assert isinstance(login_import.is_character_added_annotation, Exists)
        assert callable(login_import.get_users_with_perms)


@dataclass
class AppImport:
    app_label: str
    imports: List[LoginImport]

    def get_form_fields(self, user):
        return {
            import_.get_query_id(): forms.BooleanField(
                required=False,
                initial=True,
                label=import_.field_label
            )
            for import_ in self.imports
            if import_.check_permissions(user)
        }

    def get_imports_with_perms(self, user: User):
        return AppImport(
            self.app_label,
            [
                import_
                for import_ in self.imports
                if import_.check_permissions(user)
            ]
        )

    def has_any_perms(self, user: User):
        return any(import_.check_permissions(user) for import_ in self.imports)

    def get(self, unique_id: str) -> LoginImport:
        for import_ in self.imports:
            if import_.unique_id == unique_id:
                return import_

        raise KeyError(f"Import with unique_id {unique_id} not found")

    @staticmethod
    def validate_import(app_import: 'AppImport'):
        assert hasattr(app_import, 'app_label')
        assert hasattr(app_import, 'imports')
        assert isinstance(app_import.app_label, str)
        assert isinstance(app_import.imports, list)
        assert len(app_import.imports) > 0

        for import_ in app_import.imports:
            LoginImport.validate_import(import_)
