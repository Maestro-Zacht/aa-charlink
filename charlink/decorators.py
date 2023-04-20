from django.shortcuts import redirect
from django.contrib import messages

from esi.decorators import token_required


def charlink(func):
    def wrapper(request, *args, **kwargs):
        if 'charlink' in request.session:
            return token_required(scopes=request.session['charlink']['scopes'])(func)(request, *args, **kwargs)
        else:
            messages.error(request, 'Scopes error. Contact an administrator.')
            return redirect('charlink:index')
    return wrapper
