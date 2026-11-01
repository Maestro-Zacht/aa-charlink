from collections import defaultdict
from functools import cached_property

from django import forms

from .app_imports import import_apps
from .app_imports.utils import LoginImport


class LinkForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        imported_apps = import_apps()
        self.fields["allianceauth.authentication_default"] = forms.BooleanField(
            required=False,
            initial=True,
            disabled=True,
            label=imported_apps["allianceauth.authentication"]
            .get("default")
            .field_label,
        )
        for app, imports in imported_apps.items():
            form_fields = imports.get_form_fields(user)
            if app != "allianceauth.authentication" and len(form_fields) > 0:
                self.fields.update(form_fields)

    @cached_property
    def login_imports(self) -> list[LoginImport]:
        """Login imports matching the form fields, in field order."""
        by_id = {
            login_import.get_query_id(): login_import
            for app_import in import_apps().values()
            for login_import in app_import.imports
        }
        return [by_id[name] for name in self.fields]

    @cached_property
    def scopes_required(self) -> list[tuple[str, list[str]]]:
        """Sorted `(scope, [query_id, ...])` pairs for the form's login imports."""
        scopes = defaultdict(list)
        for login_import in self.login_imports:
            for scope in login_import.scopes:
                scopes[scope].append(login_import.get_query_id())
        return sorted(scopes.items())
