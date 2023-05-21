from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Exists, OuterRef, Q
from django.core.exceptions import PermissionDenied

from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import CharacterOwnership

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

        if user.has_perm('charlink.view_alliance'):
            queries.append(Q(alliance__alliance_id=char.alliance_id))

        if user.has_perm('charlink.view_corp') and not user.has_perm('charlink.view_alliance'):
            queries.append(Q(corporation_id=char.corporation_id))

        if user.has_perm('charlink.view_state'):
            alliances = user.profile.state.member_alliances.all()
            corporations = user.profile.state.member_corporations.all()

            queries.append(
                Q(alliance__alliance_id__in=alliances.values('alliance_id')) |
                Q(id__in=corporations)
            )

        query = queries.pop()
        for q in queries:
            query |= q

        corps = corps.filter(query)

    return corps


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

    characters = EveCharacter.objects.filter(character_ownership__user=request.user)

    characters_added = {
        'apps': [data['field_label'] for app, data in imported_apps.items() if app not in CHARLINK_IGNORE_APPS and request.user.has_perms(data['permissions'])],
        'characters': {},
    }

    for character in characters:
        characters_added['characters'][character.character_name] = []
        for app, data in imported_apps.items():
            if app not in CHARLINK_IGNORE_APPS and request.user.has_perms(data['permissions']):
                characters_added['characters'][character.character_name].append(
                    data['is_character_added'](character)
                )

    context = {
        'form': form,
        'apps': [data for app, data in imported_apps.items() if app not in CHARLINK_IGNORE_APPS and request.user.has_perms(data['permissions'])],
        'characters_added': characters_added,
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

    # if request.user.is_superuser:
    #     users = get_user_model().objects.all()
    # else:
    #     queries = []

    #     if request.user.has_perm('charlink.view_alliance'):
    #         queries.append(Q(profile__main_character__alliance_id=char.alliance_id))

    #     if request.user.has_perm('charlink.view_corp') and not request.user.has_perm('charlink.view_alliance'):
    #         queries.append(Q(profile__main_character__corporation_id=char.corporation_id))

    #     if request.user.has_perm('charlink.view_state'):
    #         alliances = request.user.profile.state.member_alliances.all()
    #         corporations = request.user.profile.state.member_corporations.all()

    #         queries.append(
    #             Q(profile__main_character__alliance_id__in=alliances.values('alliance_id')) |
    #             Q(profile__main_character__corporation_id__in=corporations.values('corporation_id'))
    #         )

    #     query = queries.pop()
    #     for q in queries:
    #         query |= q

    #     users = get_user_model().objects.filter(query)

    # users = (
    #     users
    #     .order_by(
    #         'profile__main_character__alliance_id',
    #         'profile__main_character__corporation_id'
    #     )
    #     .prefetch_related('character_ownerships__character')
    #     .select_related('profile__main_character')
    #     .distinct()
    # )

    # character_audit = {
    #     'apps': [data['field_label'] for app, data in imported_apps.items() if app not in CHARLINK_IGNORE_APPS and request.user.has_perms(data['permissions'])],
    #     'users': [],
    # }

    # for user in users:
    #     user_data = {
    #         'main_character': user.profile.main_character,
    #         'characters': {},
    #     }

    #     for ownership in user.character_ownerships.all():
    #         user_data['characters'][ownership.character.character_name] = []
    #         for app, data in imported_apps.items():
    #             if app not in CHARLINK_IGNORE_APPS and request.user.has_perms(data['permissions']):
    #                 user_data['characters'][ownership.character.character_name].append(
    #                     data['is_character_added'](ownership.character)
    #                 )

    #     character_audit['users'].append(user_data)

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
    }

    return render(request, 'charlink/audit.html', context=context)


@login_required
def search(request):
    return HttpResponse('test')
