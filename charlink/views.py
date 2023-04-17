from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .forms import LinkForm


@login_required
def index(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            pass
    else:
        form = LinkForm()

    context = {
        'form': form,
    }

    return render(request, 'charlink/charlink.html', context=context)
