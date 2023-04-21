from moonmining.models import Owner
from moonmining import __title__, tasks
from moonmining.app_settings import MOONMINING_ADMIN_NOTIFICATIONS_ENABLED

from app_utils.messages import messages_plus
from app_utils.allianceauth import notify_admins

from allianceauth.eveonline.models import EveCorporationInfo

field_label = __title__

scopes = Owner.esi_scopes()

permissions = ["moonmining.add_refinery_owner", "moonmining.basic_access"]


def add_character(request, token):
    character_ownership = request.user.character_ownerships.select_related(
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
    messages_plus.success(request, f"Update of refineres started for {owner}.")
    if MOONMINING_ADMIN_NOTIFICATIONS_ENABLED:
        notify_admins(
            message=("%(corporation)s was added as new owner by %(user)s.")
            % {"corporation": owner, "user": request.user},
            title=f"{__title__}: Owner added: {owner}",
        )
