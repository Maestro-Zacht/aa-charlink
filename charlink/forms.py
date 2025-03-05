from django import forms

from .app_imports import import_apps


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
            form_fields = imports.get_form_fields(user)
            if app != 'allianceauth.authentication' and len(form_fields) > 0:
                self.fields.update(form_fields)
