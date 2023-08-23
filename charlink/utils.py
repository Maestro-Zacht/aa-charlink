from django.db.models import Exists, OuterRef, Q
from django.contrib.auth.models import User


from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from .app_settings import CHARLINK_IGNORE_APPS
from .app_imports import import_apps


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

        if not has_access:
            query = queries.pop()
            for q in queries:
                query |= q

            corps = corps.filter(query)
        else:
            corps = corps.none()

    return corps


def chars_annotate_linked_apps(characters, apps: dict):
    for app, data in apps.items():
        characters = characters.annotate(
            **{app: data['is_character_added_annotation']}
        )

    return characters


def get_user_available_apps(user: User):
    imported_apps = import_apps()

    return {
        app: data
        for app, data in imported_apps.items()
        if app not in CHARLINK_IGNORE_APPS and user.has_perms(data['permissions'])
    }


def get_user_linked_chars(user: User):
    available_apps = get_user_available_apps(user)

    return {
        'apps': available_apps,
        'characters': chars_annotate_linked_apps(
            EveCharacter.objects.filter(character_ownership__user=user),
            available_apps
        )
    }
