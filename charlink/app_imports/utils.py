import re
from dataclasses import dataclass
from typing import Callable, List

from django.db.models import Exists, QuerySet
from django import forms
from django.contrib.auth.models import User
from django.conf import settings

from allianceauth.eveonline.models import EveCharacter
from esi.models import Token


@dataclass
class LoginImport:
    """
    The class for implementing a login import for an app.


    There can be multiple imports for an app, like in case of corptools where there is Character Audit and Corporation Audit.

    Args:
        `app_label`: The app label of the app the import is for. It must be in settings.INSTALLED_APPS and must be the same of the `AppImport`.
        `unique_id`: A unique (within the app) identifier for the import. It must be a string and contain only alphanumeric characters and no spaces.
        `field_label`: The label for the field in the form.
        `add_character`: A function that adds the character to the app. It must be a callable that takes a `esi.models.Token` as an argument and performs all the operations needed for adding a character to the application.
        `scopes`: A list of scopes required for the import.
        `check_permissions`: A function that checks if the user has permissions to use the import. It must be a callable that takes a `User` as an argument and returns a boolean.
        `is_character_added`: A function that checks if the character is already added to the app. It must be a callable that takes an EveCharacter as an argument and returns a boolean.
        `is_character_added_annotation`: A django Exists object that checks if the character is already added to the app.
        `get_users_with_perms`: A function that returns a QuerySet of users with permissions to use the import. It must be a callable that takes no arguments and returns a QuerySet of Users.
    """
    app_label: str
    unique_id: str
    field_label: str
    add_character: Callable[[Token], None]
    scopes: List[str]
    check_permissions: Callable[[User], bool]
    is_character_added: Callable[[EveCharacter], bool]
    is_character_added_annotation: Exists
    get_users_with_perms: Callable[[], QuerySet[User]]

    def get_query_id(self):
        return f"{self.app_label}_{self.unique_id}"

    def __hash__(self) -> int:
        return hash(self.get_query_id())

    def validate_import(self):
        assert hasattr(self, 'app_label')
        assert hasattr(self, 'unique_id')
        assert hasattr(self, 'field_label')
        assert hasattr(self, 'add_character')
        assert hasattr(self, 'scopes')
        assert hasattr(self, 'check_permissions')
        assert hasattr(self, 'is_character_added')
        assert hasattr(self, 'is_character_added_annotation')
        assert hasattr(self, 'get_users_with_perms')
        assert isinstance(self.app_label, str)
        assert isinstance(self.unique_id, str)
        assert re.match(r'^[a-zA-Z0-9]+$', self.unique_id) is not None
        assert isinstance(self.field_label, str)
        assert callable(self.add_character)
        assert isinstance(self.scopes, list)
        assert callable(self.check_permissions)
        assert callable(self.is_character_added)
        assert isinstance(self.is_character_added_annotation, Exists)
        assert callable(self.get_users_with_perms)


@dataclass
class AppImport:
    """
    Class wrapper for LoginImports.

    Args:
        `app_label`: The app label of the app the imports are for. It must be in settings.INSTALLED_APPS.
        `imports`: The imports for the app. Must be a list of LoginImport objects.
    """

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

    def validate_import(self):
        assert hasattr(self, 'app_label')
        assert hasattr(self, 'imports')
        assert isinstance(self.app_label, str)
        assert isinstance(self.imports, list)
        assert len(self.imports) > 0
        assert self.app_label in settings.INSTALLED_APPS

        ids = {}

        for import_ in self.imports:
            import_.validate_import()
            ids.setdefault(import_.unique_id, 0)
            ids[import_.unique_id] += 1
            assert import_.app_label == self.app_label

        for count in ids.values():
            assert count == 1
