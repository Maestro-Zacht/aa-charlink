from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404

from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.decorators import permissions_required

from app_utils.allianceauth import users_with_permission

from .forms import LinkForm
from .app_imports import import_apps
from .decorators import charlink
from .app_settings import CHARLINK_IGNORE_APPS
from .utils import get_user_available_apps, get_user_linked_chars, get_visible_corps, chars_annotate_linked_apps

logger = get_extension_logger(__name__)


def get_navbar_elements(user: User):
    is_auditor = user.has_perm('charlink.view_state') or user.has_perm('charlink.view_corp') or user.has_perm('charlink.view_alliance')

    return {
        'is_auditor': is_auditor,
        'available_apps': get_user_available_apps(user) if is_auditor else [],
        'available': get_visible_corps(user) if is_auditor else [],
    }


@login_required
def index(request):
    imported_apps = import_apps()

    if request.method == 'POST':
        form = LinkForm(request.user, request.POST)
        if form.is_valid():

            scopes = set()
            selected_apps = []

            for import_code, to_import in form.cleaned_data.items():
                if to_import:
                    app, unique_id = import_code.split('-')
                    app_import = imported_apps[app].get(unique_id)
                    scopes.update(app_import.scopes)
                    selected_apps.append(app_import)

            request.session['charlink'] = {
                'scopes': list(scopes),
                'imports': selected_apps,
            }

            return redirect('charlink:login')

    else:
        form = LinkForm(request.user)

    context = {
        'form': form,
        'characters_added': get_user_linked_chars(request.user),
        **get_navbar_elements(request.user),
    }

    return render(request, 'charlink/charlink.html', context=context)


@login_required
@charlink
def login_view(request, token):
    charlink_data = request.session.pop('charlink')

    for import_ in charlink_data['imports']:
        if import_.app_label != 'add_character' and import_.app_label not in CHARLINK_IGNORE_APPS and request.user.has_perms(import_.permissions):
            try:
                import_.add_character(request, token)
            except Exception as e:
                logger.exception(e)
                messages.error(request, f"Failed to add character to {import_.field_label}")
            else:
                messages.success(request, f"Character successfully added to {import_.field_label}")

    return redirect('charlink:index')


@login_required
@permissions_required([
    'charlink.view_corp',
    'charlink.view_alliance',
    'charlink.view_state',
])
def audit(request, corp_id: int):
    corp = get_object_or_404(EveCorporationInfo, corporation_id=corp_id)
    corps = get_visible_corps(request.user)

    if not corps.filter(corporation_id=corp_id).exists():
        raise PermissionDenied('You do not have permission to view the selected corporation statistics.')

    context = {
        'selected': corp,
        **get_navbar_elements(request.user),
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
        **get_navbar_elements(request.user),
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
        **get_navbar_elements(request.user),
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

    users = [
        users_with_permission(
            Permission.objects.get(
                content_type__app_label=perm.split('.')[0],
                codename=perm.split('.')[1]
            )
        )
        for perm in app_data['permissions']
    ]

    if len(users) == 0:
        perm_query = Q(character_ownership__isnull=False)
    else:
        user_query = users.pop()
        for query in users:
            user_query &= query

        perm_query = Q(character_ownership__user__in=user_query)

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
        'app': app,
        'app_data': app_data,
        **get_navbar_elements(request.user),
    }

    return render(request, 'charlink/app_audit.html', context=context)
