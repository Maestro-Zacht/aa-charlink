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
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            imported_apps = import_apps()
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
        form = LinkForm()

    context = {
        'form': form,
    }

    return render(request, 'charlink/charlink.html', context=context)


@login_required
@charlink
def login_view(request, token):
    imported_apps = import_apps()

    charlink_data = request.session.pop('charlink')

    for app in charlink_data['apps']:
        if app != 'add_character':
            # messages.success(request, f"Linking {request.user} to {app}")
            imported_apps[app]['add_character'](request, token)

    return redirect('authentication:dashboard')
