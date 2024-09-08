from django.db.models import Exists, OuterRef
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import CharacterOwnership

from charlink.app_imports.utils import LoginImport, AppImport


app_import = AppImport('allianceauth.authentication', [
    LoginImport(
        app_label='allianceauth.authentication',
        unique_id='default',
        field_label=_('Add Character (default)'),
        add_character=lambda request, token: None,
        scopes=['publicData'],
        check_permissions=lambda user: True,
        is_character_added=lambda character: CharacterOwnership.objects.filter(character=character).exists(),
        is_character_added_annotation=Exists(CharacterOwnership.objects.filter(character_id=OuterRef('pk'))),
        get_users_with_perms=lambda: User.objects.filter(
            Exists(CharacterOwnership.objects.filter(user_id=OuterRef('pk')))
        ),
    )
])
