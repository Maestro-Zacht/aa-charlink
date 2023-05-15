from django import forms

from .app_imports import import_apps
from .app_settings import CHARLINK_IGNORE_APPS


class LinkForm(forms.Form):
    add_character = forms.BooleanField(
        required=False,
        initial=True,
        disabled=True,
        label='Add Character (default)'
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for app, data in import_apps().items():
            if app != 'add_character' and app not in CHARLINK_IGNORE_APPS and user.has_perms(data['permissions']):
                self.fields[app] = forms.BooleanField(
                    required=False,
                    initial=True,
                    label=data.get('field_label', app)
                )
