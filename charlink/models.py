from django.db import models


class General(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('view_corp', 'Can view linked character of members of their corporation.'),
            ('view_alliance', 'Can view linked character of members of their alliance.'),
            ('view_state', 'Can view linked character of members of their auth state.'),
        )
