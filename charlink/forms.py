from django import forms

from .app_imports import import_apps
from .app_settings import CHARLINK_IGNORE_APPS


class LinkForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        imported_apps = import_apps()
        self.fields['allianceauth.authentication_default'] = forms.BooleanField(
            required=False,
            initial=True,
            disabled=True,
            label=imported_apps['allianceauth.authentication'].get('default').field_label
        )
        for app, imports in imported_apps.items():
            if app != 'allianceauth.authentication' and app not in CHARLINK_IGNORE_APPS:
                self.fields.update(imports.get_form_fields(user))
