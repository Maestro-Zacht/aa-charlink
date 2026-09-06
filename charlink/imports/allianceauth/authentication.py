from allianceauth.authentication.models import CharacterOwnership
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

from charlink.app_imports.utils import AppImport, LoginImport

app_import = AppImport(
    "allianceauth.authentication",
    [
        LoginImport(
            app_label="allianceauth.authentication",
            unique_id="default",
            field_label=_("Add Character (default)"),
            add_character=lambda request, token: None,  # noqa: ARG005
            scopes=["publicData"],
            check_permissions=lambda user: True,  # noqa: ARG005
            is_character_added=lambda character: CharacterOwnership.objects.filter(
                character=character
            ).exists(),
            is_character_added_annotation=Exists(
                CharacterOwnership.objects.filter(character_id=OuterRef("pk"))
            ),
            get_users_with_perms=lambda: User.objects.filter(
                Exists(CharacterOwnership.objects.filter(user_id=OuterRef("pk")))
            ),
        )
    ],
)
