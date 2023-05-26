from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib import messages
from django.db.models import Exists, OuterRef, Q
from django.core.exceptions import PermissionDenied
from django.http import Http404

from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import CharacterOwnership

from app_utils.allianceauth import users_with_permission

from .forms import LinkForm
from .app_imports import import_apps
from .decorators import charlink
from .app_settings import CHARLINK_IGNORE_APPS

logger = get_extension_logger(__name__)


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


@login_required
def index(request):
    imported_apps = import_apps()

    if request.method == 'POST':
        form = LinkForm(request.user, request.POST)
        if form.is_valid():

            scopes = set()
            selected_apps = []

            for app, to_import in form.cleaned_data.items():
                if to_import:
                    scopes.update(imported_apps[app].get('scopes', []))
                    selected_apps.append(app)

            logger.debug(f"Scopes: {scopes}")

            request.session['charlink'] = {
                'scopes': list(scopes),
                'apps': selected_apps,
            }

            return redirect('charlink:login')

    else:
        form = LinkForm(request.user)

    context = {
        'form': form,
        'characters_added': get_user_linked_chars(request.user),
        'is_auditor': request.user.has_perm('charlink.view_state') or request.user.has_perm('charlink.view_corp') or request.user.has_perm('charlink.view_alliance'),
    }

    return render(request, 'charlink/charlink.html', context=context)


@login_required
@charlink
def login_view(request, token):
    imported_apps = import_apps()

    charlink_data = request.session.pop('charlink')

    for app in charlink_data['apps']:
        if app != 'add_character' and app not in CHARLINK_IGNORE_APPS and request.user.has_perms(imported_apps[app]['permissions']):
            try:
                imported_apps[app]['add_character'](request, token)
            except Exception as e:
                logger.exception(e)
                messages.error(request, f"Failed to add character to {imported_apps[app]['field_label']}")
            else:
                messages.success(request, f"Character successfully added to {imported_apps[app]['field_label']}")

    return redirect('charlink:index')


@login_required
@permissions_required([
    'charlink.view_corp',
    'charlink.view_alliance',
    'charlink.view_state',
])
def audit(request, corp_id=None):
    char = request.user.profile.main_character
    if corp_id:
        corp = get_object_or_404(EveCorporationInfo, corporation_id=corp_id)
    else:
        corp = None

    corps = get_visible_corps(request.user)

    if corp_id and corp not in corps:
        raise PermissionDenied('You do not have permission to view the selected corporation statistics.')

    if not corp_id and corps.count() == 1:
        corp = corps.first()
    elif not corp_id and char:
        try:
            corp = corps.get(corporation_id=char.corporation_id)
        except EveCorporationInfo.DoesNotExist:
            pass

    context = {
        'available': corps,
        'selected': corp,
        'available_apps': get_user_available_apps(request.user),
    }

    return render(request, 'charlink/audit.html', context=context)


@login_required
@permissions_required([
    'charlink.view_corp',
    'charlink.view_alliance',
    'charlink.view_state',
])
def search(request):
    search_string = request.GET.get('search_string', None)
    if not search_string:
        return redirect('charlink:index')

    corps = get_visible_corps(request.user)

    characters = (
        EveCharacter.objects
        .filter(
            character_name__icontains=search_string,
            corporation_id__in=corps.values('corporation_id'),
        )
        .order_by('character_name')
        .select_related('character_ownership__user__profile__main_character')
    )

    context = {
        'search_string': search_string,
        'characters': characters,
        'available': corps,
        'available_apps': get_user_available_apps(request.user),
    }

    return render(request, 'charlink/search.html', context=context)


@login_required
@permissions_required([
    'charlink.view_corp',
    'charlink.view_alliance',
    'charlink.view_state',
])
def audit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    corps = get_visible_corps(request.user)

    if (
        not request.user.is_superuser
        and
        user != request.user
        and
        not corps
        .filter(
            corporation_id=user.profile.main_character.corporation_id
        )
        .exists()
    ):
        raise PermissionDenied('You do not have permission to view the selected user statistics.')

    context = {
        'characters_added': get_user_linked_chars(user),
        'available': corps,
        'available_apps': get_user_available_apps(user),
    }

    return render(request, 'charlink/user_audit.html', context=context)


@login_required
@permissions_required([
    'charlink.view_corp',
    'charlink.view_alliance',
    'charlink.view_state',
])
def audit_app(request, app):
    imported_apps = import_apps()

    if app not in imported_apps:
        raise Http404()

    app_data = imported_apps[app]

    if not request.user.has_perms(app_data['permissions']):
        raise PermissionDenied('You do not have permission to view the selected application statistics.')

    corps = get_visible_corps(request.user)

    queries = []
    for perm in app_data['permissions']:
        app_label, codename = perm.split('.')
        perm_obj = Permission.objects.get(content_type__app_label=app_label, codename=codename)

        queries.append(Q(character_ownership__user__in=users_with_permission(perm_obj)))

    if len(queries) == 0:
        perm_query = Q(character_ownership__isnull=False)
    else:
        perm_query = queries.pop()
        for query in queries:
            perm_query |= query

    visible_characters = EveCharacter.objects.filter(
        (
            Q(corporation_id__in=corps.values('corporation_id')) |
            Q(character_ownership__user__profile__main_character__corporation_id__in=corps.values('corporation_id'))
        ) &
        perm_query,
    ).select_related('character_ownership__user__profile__main_character')

    visible_characters = chars_annotate_linked_apps(
        visible_characters,
        {app: app_data}
    ).order_by(app, 'character_name')

    context = {
        'characters': visible_characters,
        'available': corps,
        'app': app,
        'app_data': app_data,
        'available_apps': get_user_available_apps(request.user),
    }

    return render(request, 'charlink/app_audit.html', context=context)
