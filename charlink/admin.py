from django.apps import apps
from django.contrib import admin

from .models import ComplianceFilter


class ComplianceFilterAdmin(admin.ModelAdmin):
    filter_horizontal = ('selected_apps',)


if apps.is_installed('securegroups'):
    admin.site.register(ComplianceFilter, ComplianceFilterAdmin)
