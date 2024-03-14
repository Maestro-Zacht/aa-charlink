import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.loader import render_to_string

from allianceauth.services.hooks import get_extension_logger
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.authentication.decorators import permissions_required

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


def dashboard_login(request):
    form = LinkForm(request.user, prefix='charlink')
    context = {
        'form': form,
    }
    return render_to_string('charlink/dashboard_login.html', context=context, request=request)


@login_required
def dashboard_post(request):
    if request.method != 'POST':
        messages.error(request, 'Invalid request')
        return redirect('charlink:index')

    imported_apps = import_apps()

    form = LinkForm(request.user, request.POST, prefix='charlink')
    if not form.is_valid():
        messages.error(request, 'Invalid form data')
        return redirect('authentication:dashboard')

    scopes = set()
    selected_apps = []

    form_field_pattern = re.compile(r'^(?P<app>[\w\d\.]+)_(?P<unique_id>[a-zA-Z0-9]+)$')

    for import_code, to_import in form.cleaned_data.items():
        if to_import:
            match = form_field_pattern.match(import_code)

            app = match.group('app')
            unique_id = match.group('unique_id')

            app_import = imported_apps[app].get(unique_id)
            scopes.update(app_import.scopes)
            selected_apps.append((app, unique_id))

    request.session['charlink'] = {
        'scopes': list(scopes),
        'imports': selected_apps,
    }

    return redirect('charlink:login')


@login_required
def index(request):
    imported_apps = import_apps()

    if request.method == 'POST':
        form = LinkForm(request.user, request.POST)
        if form.is_valid():
            scopes = set()
            selected_apps = []

            form_field_pattern = re.compile(r'^(?P<app>[\w\d\.]+)_(?P<unique_id>[a-zA-Z0-9]+)$')

            for import_code, to_import in form.cleaned_data.items():
                if to_import:
                    match = form_field_pattern.match(import_code)

                    app = match.group('app')
                    unique_id = match.group('unique_id')

                    app_import = imported_apps[app].get(unique_id)
                    scopes.update(app_import.scopes)
                    selected_apps.append((app, unique_id))

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
    imported_apps = import_apps()

    charlink_data = request.session.pop('charlink')

    for app, unique_id in charlink_data['imports']:
        import_ = imported_apps[app].get(unique_id)
        if app != 'allianceauth.authentication' and app not in CHARLINK_IGNORE_APPS and import_.check_permissions(request.user):
            try:
                import_.add_character(token)
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

    app_imports = imported_apps[app]

    if not app_imports.has_any_perms(request.user):
        raise PermissionDenied('You do not have permission to view the selected application statistics.')

    app_imports = app_imports.get_imports_with_perms(request.user)

    corp_ids = get_visible_corps(request.user).values('corporation_id')

    logins = {}

    for import_ in app_imports.imports:
        visible_characters = EveCharacter.objects.filter(
            (
                Q(corporation_id__in=corp_ids) |
                Q(character_ownership__user__profile__main_character__corporation_id__in=corp_ids)
            ) &
            Q(character_ownership__user__in=import_.get_users_with_perms()),
        ).select_related('character_ownership__user__profile__main_character')

        visible_characters = chars_annotate_linked_apps(
            visible_characters,
            [import_]
        ).order_by(import_.get_query_id(), 'character_name')

        logins[import_] = visible_characters

    context = {
        'logins': logins,
        'app': app,
        **get_navbar_elements(request.user),
    }

    return render(request, 'charlink/app_audit.html', context=context)
