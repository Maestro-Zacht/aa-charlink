from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from moonmining.models import Owner
from moonmining import __title__, tasks
from moonmining.app_settings import MOONMINING_ADMIN_NOTIFICATIONS_ENABLED

from app_utils.allianceauth import notify_admins

from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character(token):
    character_ownership = token.user.character_ownerships.select_related(
        "character"
    ).get(character__character_id=token.character_id)

    try:
        corporation = EveCorporationInfo.objects.get(
            corporation_id=character_ownership.character.corporation_id
        )
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(
            corp_id=character_ownership.character.corporation_id
        )
        corporation.save()

    owner, _ = Owner.objects.update_or_create(
        corporation=corporation,
        defaults={"character_ownership": character_ownership},
    )
    tasks.update_owner.delay(owner.pk)
    if MOONMINING_ADMIN_NOTIFICATIONS_ENABLED:
        notify_admins(
            message=("%(corporation)s was added as new owner by %(user)s.")
            % {"corporation": owner, "user": token.user},
            title=f"{__title__}: Owner added: {owner}",
        )


def _is_character_added(character: EveCharacter):
    return Owner.objects.filter(
        character_ownership__character=character
    ).exists()


def _users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='moonmining',
            codename='add_refinery_owner'
        )
    ) & users_with_permission(
        Permission.objects.get(
            content_type__app_label='moonmining',
            codename='basic_access'
        )
    )


app_import = AppImport('moonmining', [
    LoginImport(
        app_label='moonmining',
        unique_id='default',
        field_label=__title__,
        add_character=_add_character,
        scopes=Owner.esi_scopes(),
        check_permissions=lambda user: user.has_perms(["moonmining.add_refinery_owner", "moonmining.basic_access"]),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            Owner.objects
            .filter(character_ownership__character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
])
