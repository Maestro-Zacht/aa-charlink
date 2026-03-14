from typing import List
from functools import reduce
import operator

from django.db.models import Exists, OuterRef, Q
from django.contrib.auth.models import User

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

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
        if imports.has_any_perms(user)
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


def _get_single_perm_q(perm):
    try:
        app_label, codename = perm.split('.')
    except ValueError:
        raise ValueError(f"Permission '{perm}' must be in 'app_label.codename' format")

    return (
        Q(user_permissions__content_type__app_label=app_label, user_permissions__codename=codename) |
        Q(groups__permissions__content_type__app_label=app_label, groups__permissions__codename=codename) |
        Q(profile__state__permissions__content_type__app_label=app_label, profile__state__permissions__codename=codename)
    )


def permissions_q(perms: list[str], require_all=True):
    """
    Returns a Q object that filters users by a list of permissions. It needs to be used with distinct: `User.objects.filter(permissions_q(perms)).distinct()`

    :param perms: List of strings in 'app_label.codename' format.
    :param require_all: True for AND logic (must have all permissions), False for OR logic (must have any permission).
    """
    if isinstance(perms, str):
        perms = [perms]

    if not perms:
        return Q()

    superuser_q = Q(is_superuser=True)

    if require_all:
        subqueries = [
            Q(pk__in=User.objects.filter(_get_single_perm_q(p)).values('pk'))
            for p in perms
        ]

        res_q = reduce(operator.and_, subqueries) | superuser_q
    else:
        combined_perms_q = reduce(operator.or_, (_get_single_perm_q(p) for p in perms))
        res_q = combined_perms_q | superuser_q

    return res_q


def users_with_permissions(perms: list[str], require_all=True):
    """
    Returns a queryset of users that have the specified permissions. It includes superusers.

    :param perms: List of strings in 'app_label.codename' format.
    :param require_all: True for AND logic (must have all permissions), False for OR logic (must have any permission).
    """
    return User.objects.filter(permissions_q(perms, require_all)).distinct()
