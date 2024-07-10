from django.db.models import Exists, OuterRef
from django.contrib.auth.models import Permission

from django.utils import translation
from django.utils.translation import gettext as _
from django.utils.html import format_html
from django.contrib import messages


from structures import __title__, tasks
from structures.models import Owner, Webhook, OwnerCharacter
from structures.app_settings import (
    STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED,
    STRUCTURES_DEFAULT_LANGUAGE,
)

from app_utils.allianceauth import notify_admins
from app_utils.allianceauth import users_with_permission

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.models import CharacterOwnership

from charlink.app_imports.utils import LoginImport, AppImport


def _add_character(request, token):
    token_char = EveCharacter.objects.get(character_id=token.character_id)
    character_ownership = CharacterOwnership.objects.get(
        user=request.user, character=token_char
    )

    try:
        corporation = EveCorporationInfo.objects.get(
            corporation_id=token_char.corporation_id
        )
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(
            token_char.corporation_id
        )
    owner, created = Owner.objects.update_or_create(
        corporation=corporation, defaults={"is_active": True}
    )
    owner.add_character(character_ownership)
    if created:
        default_webhooks = Webhook.objects.filter(is_default=True)
        if default_webhooks:
            for webhook in default_webhooks:
                owner.webhooks.add(webhook)
            owner.save()

    if owner.characters.count() == 1:
        tasks.update_all_for_owner.delay(owner_pk=owner.pk, user_pk=request.user.pk)
        messages.info(
            request,
            format_html(
                _(
                    "%(corporation)s has been added with %(character)s "
                    "as sync character. "
                    "We have started fetching structures and notifications "
                    "for this corporation and you will receive a report once "
                    "the process is finished."
                )
                % {"corporation": owner, "character": token_char}
            ),
        )

        if STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED:
            with translation.override(STRUCTURES_DEFAULT_LANGUAGE):
                notify_admins(
                    message=_(
                        "%(corporation)s was added as new "
                        "structure owner by %(user)s."
                    )
                    % {"corporation": owner, "user": token.user.username},
                    title=_("%s: Structure owner added: %s") % (__title__, owner),
                )
    else:
        messages.info(
            request,
            format_html(
                _(
                    "%(character)s has been added to %(corporation)s "
                    "as sync character. "
                    "You now have %(characters_count)d sync character(s) configured."
                )
                % {
                    "corporation": owner,
                    "character": token_char,
                    "characters_count": owner.valid_characters_count(),
                }
            ),
        )
        if STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED:
            with translation.override(STRUCTURES_DEFAULT_LANGUAGE):
                notify_admins(
                    message=_(
                        "%(character)s was added as sync character to "
                        "%(corporation)s by %(user)s.\n"
                        "We now have %(characters_count)d sync character(s) configured."
                    )
                    % {
                        "character": token_char,
                        "corporation": owner,
                        "user": request.user.username,
                        "characters_count": owner.valid_characters_count(),
                    },
                    title=_("%s: Character added to: %s") % (__title__, owner),
                )


def _is_character_added(character: EveCharacter):
    return OwnerCharacter.objects.filter(
        character_ownership__character=character
    ).exists()


def _users_with_perms():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label='structures',
            codename='add_structure_owner'
        )
    )


app_import = AppImport('structures', [
    LoginImport(
        app_label='structures',
        unique_id='default',
        field_label=__title__,
        add_character=_add_character,
        scopes=Owner.get_esi_scopes(),
        check_permissions=lambda user: user.has_perm("structures.add_structure_owner"),
        is_character_added=_is_character_added,
        is_character_added_annotation=Exists(
            OwnerCharacter.objects
            .filter(character_ownership__character_id=OuterRef('pk'))
        ),
        get_users_with_perms=_users_with_perms,
    ),
])
