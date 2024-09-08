from django.db.models import Exists, OuterRef
from django.contrib.auth.models import User

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import AppImport, LoginImport

app_import = AppImport(
    'fakeapp',
    [
        LoginImport(
            app_label='fakeapp',
            unique_id='invalid id',
            field_label='TestApp',
            add_character=lambda request, user: None,
            scopes=['esi-characters.read_loyalty.v1'],
            check_permissions=lambda user: True,
            is_character_added=lambda character: True,
            is_character_added_annotation=Exists(EveCharacter.objects.filter(character_id=OuterRef('character_id'))),
            get_users_with_perms=lambda: User.objects.all()
        ),
    ]
)
