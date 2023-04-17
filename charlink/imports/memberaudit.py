from django.db import transaction

from memberaudit.models import Character, ComplianceGroupDesignation
from memberaudit.app_settings import MEMBERAUDIT_APP_NAME, MEMBERAUDIT_TASKS_NORMAL_PRIORITY
from memberaudit import tasks

from allianceauth.eveonline.models import EveCharacter

field_label = MEMBERAUDIT_APP_NAME

scopes = Character.get_esi_scopes()

permissions = ["memberaudit.basic_access"]


def add_character(request, token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, created = Character.objects.update_or_create(
            eve_character=eve_character, defaults={"is_disabled": False}
        )
    tasks.update_character.apply_async(
        kwargs={"character_pk": character.pk},
        priority=MEMBERAUDIT_TASKS_NORMAL_PRIORITY,
    )
    if ComplianceGroupDesignation.objects.exists():
        tasks.update_compliance_groups_for_user.apply_async(
            args=[request.user.pk], priority=MEMBERAUDIT_TASKS_NORMAL_PRIORITY
        )
