from collections import defaultdict

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as gl

from allianceauth.eveonline.models import EveCharacter


class General(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('view_corp', 'Can view linked character of members of their corporation.'),
            ('view_alliance', 'Can view linked character of members of their alliance.'),
            ('view_state', 'Can view linked character of members of their auth state.'),
            ('view_admin', 'Can view CharLink Admin page.'),
        )


class AppSettings(models.Model):
    app_name = models.CharField(max_length=255, unique=True)

    ignored = models.BooleanField(default=False)
    default_selection = models.BooleanField(default=True)

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        from .app_imports import import_apps
        imported_apps = import_apps()
        app, _, unique_id = self.app_name.rpartition('_')
        login_import = imported_apps[app].get(unique_id)
        return str(login_import.field_label) if login_import else self.app_name


# Smart filters

class BaseFilter(models.Model):
    name = models.CharField(max_length=500)  # This is the filters name shown to the admin
    description = models.CharField(max_length=500)  # this is what is shown to the user

    class Meta:
        abstract = True
        default_permissions = ()

    def __str__(self):
        return f"{self.name}: {self.description}"

    def process_filter(self, user: User):  # Single User Pass Fail system
        raise NotImplementedError("Please Create a filter!")

    def audit_filter(self, users):  # Bulk check system that also advises the user with simple messages
        raise NotImplementedError("Please Create an audit function!")


class ComplianceFilter(BaseFilter):
    selected_apps = models.ManyToManyField(AppSettings, related_name='+')

    negate = models.BooleanField(default=False)

    class Meta:
        verbose_name = gl("Smart Filter: Compliance")
        verbose_name_plural = verbose_name
        default_permissions = ()

    def process_filter(self, user: User):
        return self.audit_filter(User.objects.filter(pk=user.pk))[user.pk]['check']

    def audit_filter(self, users):
        from .app_imports import import_apps

        output = defaultdict(lambda: {"message": "", "check": False})
        imported_apps = import_apps()

        queries = []

        for selected_app in self.selected_apps.all():
            app, _, unique_id = selected_app.app_name.rpartition('_')
            try:
                login_import = imported_apps[app].get(unique_id)
            except KeyError:
                return output
            queries.append(login_import.is_character_added_annotation)

        chars = EveCharacter.objects.filter(
            character_ownership__user__in=users
        )

        q = queries[0]
        for query in queries[1:]:
            q = q & query

        chars = (
            chars
            .annotate(has_compliance=q)
            .values(user_pk=models.F('character_ownership__user'))
            .annotate(
                has_compliance=models.Sum('has_compliance', output_field=models.IntegerField())
            )
            .annotate(char_count=models.Count('*'))
        )

        for user_data in chars:
            compliance = user_data['has_compliance'] == user_data['char_count']
            output[user_data['user_pk']] = {
                "message": gl("Meets requirements") if compliance else gl("Does not meet requirements"),
                "check": compliance ^ self.negate
            }

        return output
