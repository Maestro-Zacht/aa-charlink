from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from moonstuff.providers import ESI_CHARACTER_SCOPES
from moonstuff.models import TrackingCharacter
from moonstuff.tasks import import_extraction_data

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport
from charlink.utils import users_with_permissions


def _add_character(request, token):
    eve_char = EveCharacter.objects.get(character_id=token.character_id)

    if not TrackingCharacter.objects.filter(character=eve_char).exists():
        char = TrackingCharacter(character=eve_char)
        char.save()

        # Schedule an import task to pull data from the new Tracking Character.
        import_extraction_data.delay()
    else:
        assert False


def _is_character_added(character: EveCharacter):
    return TrackingCharacter.objects.filter(character=character).exists()


def _users_with_perms():
    return users_with_permissions('moonstuff.add_trackingcharacter', require_all=False)


app_import = AppImport('moonstuff', [
    LoginImport(
        app_label='moonstuff',
        unique_id='default',
        field_label='Moon Tools',
        add_character=_add_character,
        scopes=ESI_CHARACTER_SCOPES,
        check_permissions=lambda user: user.has_perm('moonstuff.add_trackingcharacter'),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            TrackingCharacter.objects
            .filter(character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms,
        default_initial_selection=False,
    ),
])
