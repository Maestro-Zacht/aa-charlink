from django.db import transaction
from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from miningtaxes.models import Character, Stats, AdminCharacter
from miningtaxes import tasks

from allianceauth.eveonline.models import EveCharacter

from charlink.app_imports.utils import LoginImport, AppImport

from app_utils.allianceauth import users_with_permission


def _add_character_basic(request, token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, _ = Character.objects.update_or_create(eve_character=eve_character)
    tasks.update_character.delay(character_pk=character.pk)
    messages.success(
        request,
        format_html(
            "<strong>{}</strong> has been registered. "
            "Note that it can take a minute until all character data is visible.",
            eve_character,
        ),
    )
    s = Stats.load()
    s.calc_admin_main_json()


def _add_character_admin(request, token):
    eve_character = EveCharacter.objects.get(character_id=token.character_id)
    with transaction.atomic():
        character, _ = AdminCharacter.objects.update_or_create(
            eve_character=eve_character
        )
    tasks.update_admin_character.delay(character_pk=character.pk)
    messages.success(
        request,
        format_html(
            "<strong>{}</strong> has been registered. "
            "Note that it can take a minute until all character data is visible.",
            eve_character,
        ),
    )


def _is_character_added_basic(character: EveCharacter):
    return Character.objects.filter(eve_character=character).exists()


def _is_character_added_admin(character: EveCharacter):
    return AdminCharacter.objects.filter(eve_character=character).exists()


def _users_with_perms_basic():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='miningtaxes',
            codename='basic_access'
        )
    )


def _users_with_perms_admin():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='miningtaxes',
            codename='admin_access'
        )
    )


app_import = AppImport('miningtaxes', [
    LoginImport(
        app_label='miningtaxes',
        unique_id='default',
        field_label=_("Mining Taxes"),
        add_character=_add_character_basic,
        scopes=Character.get_esi_scopes(),
        check_permissions=lambda user: user.has_perm("miningtaxes.basic_access"),
        is_character_added=_is_character_added_basic,
        is_character_added_annotation=Exists(
            Character.objects
            .filter(eve_character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms_basic,
    ),
    LoginImport(
        app_label='miningtaxes',
        unique_id='admin',
        field_label=_("Mining Taxes Admin"),
        add_character=_add_character_admin,
        scopes=AdminCharacter.get_esi_scopes(),
        check_permissions=lambda user: user.has_perm("miningtaxes.admin_access"),
        is_character_added=_is_character_added_admin,
        is_character_added_annotation=Exists(
            AdminCharacter.objects
            .filter(eve_character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms_admin,
    ),
])
