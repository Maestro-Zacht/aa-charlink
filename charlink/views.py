from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from allianceauth.services.hooks import get_extension_logger

from .forms import LinkForm
from .app_imports import import_apps
from .decorators import charlink

logger = get_extension_logger(__name__)


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
        'apps': {app: data for app, data in imported_apps.items() if app != 'add_character' and request.user.has_perms(data['permissions'])},
    }

    return render(request, 'charlink/charlink.html', context=context)


@login_required
@charlink
def login_view(request, token):
    imported_apps = import_apps()

    charlink_data = request.session.pop('charlink')

    for app in charlink_data['apps']:
        if app != 'add_character' and request.user.has_perms(imported_apps[app]['permissions']):
            try:
                imported_apps[app]['add_character'](request, token)
            except Exception as e:
                logger.exception(e)
                messages.error(request, f"Failed to add character to {imported_apps[app]['field_label']}")
            else:
                messages.success(request, f"Character successfully added to {imported_apps[app]['field_label']}")

    return redirect('authentication:dashboard')
