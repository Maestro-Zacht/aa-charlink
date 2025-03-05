from django.db import models


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
        return self.app_name
