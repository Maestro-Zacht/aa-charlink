from typing import List

from django.db.models import Exists, OuterRef, Q
from django.contrib.auth.models import User

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from .app_settings import CHARLINK_IGNORE_APPS
from .app_imports import import_apps
from .app_imports.utils import LoginImport


def get_visible_corps(user: User):
    char = user.profile.main_character

    corps = EveCorporationInfo.objects.filter(
        Exists(
            CharacterOwnership.objects
            .filter(character__corporation_id=OuterRef('corporation_id'))
        )
    )

    if user.is_superuser:
        corps = corps.all()
    else:
        queries = []
        has_access = False

        if user.has_perm('charlink.view_alliance'):
            queries.append(Q(alliance__alliance_id=char.alliance_id))
            has_access = True

        if user.has_perm('charlink.view_corp') and not user.has_perm('charlink.view_alliance'):
            queries.append(Q(corporation_id=char.corporation_id))
            has_access = True

        if user.has_perm('charlink.view_state'):
            alliances = user.profile.state.member_alliances.all()
            corporations = user.profile.state.member_corporations.all()

            queries.append(
                Q(alliance__alliance_id__in=alliances.values('alliance_id')) |
                Q(id__in=corporations)
            )
            has_access = True

        if has_access:
            query = queries.pop()
            for q in queries:
                query |= q

            corps = corps.filter(query)
        else:
            corps = corps.none()

    return corps


def chars_annotate_linked_apps(characters, imports: List[LoginImport]):
    for import_ in imports:
        characters = characters.annotate(
            **{import_.get_query_id(): import_.is_character_added_annotation}
        )

    return characters


def get_user_available_apps(user: User):
    imported_apps = import_apps()

    return {
        app: imports.get_imports_with_perms(user)
        for app, imports in imported_apps.items()
        if app not in CHARLINK_IGNORE_APPS and imports.has_any_perms(user)
    }


def get_user_linked_chars(user: User):
    available_apps = get_user_available_apps(user)

    return {
        'apps': available_apps,
        'characters': chars_annotate_linked_apps(
            EveCharacter.objects.filter(character_ownership__user=user),
            [
                import_
                for imports in available_apps.values()
                for import_ in imports.get_imports_with_perms(user).imports
            ]
        )
    }
