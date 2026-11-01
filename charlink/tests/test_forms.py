from unittest.mock import patch

from allianceauth.tests.auth_utils import AuthUtils
from django.db.models import Q
from django.test import TestCase

from charlink.app_imports import import_apps
from charlink.forms import LinkForm
from charlink.models import AppSettings
from charlink.tests.factories import create_user_main


@patch("charlink.app_imports._imported", False)
@patch("charlink.app_imports._duplicated_apps", set())
@patch("charlink.app_imports._supported_apps", {})
@patch("charlink.app_imports._failed_to_import", {})
@patch("charlink.app_imports._no_import", [])
class TestLinkForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user_main()

    def test_init_no_perms(self):
        import_apps()
        form = LinkForm(self.user)
        self.assertIn("allianceauth.authentication_default", form.fields)
        self.assertNotIn("allianceauth.corputils_default", form.fields)

    def test_init_with_perms(self):
        import_apps()
        user = AuthUtils.add_permissions_to_user_by_name(
            ["corputils.add_corpstats", "marketmanager.basic_market_browser"], self.user
        )
        form = LinkForm(user)
        self.assertIn("allianceauth.authentication_default", form.fields)
        self.assertIn("allianceauth.corputils_default", form.fields)
        self.assertIn("marketmanager_corporation", form.fields)
        self.assertIn("marketmanager_character", form.fields)

    def test_init_with_perms_ignore(self):
        import_apps()
        AppSettings.objects.filter(
            Q(app_name="allianceauth.corputils_default")
            | Q(app_name="marketmanager_corporation")
        ).update(ignored=True)

        user = AuthUtils.add_permissions_to_user_by_name(
            ["corputils.add_corpstats", "marketmanager.basic_market_browser"], self.user
        )
        form = LinkForm(user)
        self.assertIn("allianceauth.authentication_default", form.fields)
        self.assertNotIn("allianceauth.corputils_default", form.fields)
        self.assertNotIn("marketmanager_corporation", form.fields)
        self.assertIn("marketmanager_character", form.fields)

    def test_login_imports(self):
        import_apps()
        user = AuthUtils.add_permissions_to_user_by_name(
            ["marketmanager.basic_market_browser"], self.user
        )
        form = LinkForm(user)

        query_ids = [login_import.get_query_id() for login_import in form.login_imports]
        self.assertListEqual(query_ids, list(form.fields))
        self.assertEqual(query_ids[0], "allianceauth.authentication_default")
        self.assertIn("marketmanager_character", query_ids)
        self.assertIn("marketmanager_corporation", query_ids)
        self.assertNotIn("allianceauth.corputils_default", query_ids)

    def test_scopes_required(self):
        import_apps()
        user = AuthUtils.add_permissions_to_user_by_name(
            ["marketmanager.basic_market_browser"], self.user
        )
        form = LinkForm(user)

        scopes = [scope for scope, _ in form.scopes_required]
        self.assertListEqual(scopes, sorted(set(scopes)))

        scopes_required = dict(form.scopes_required)
        for login_import in form.login_imports:
            for scope in login_import.scopes:
                self.assertIn(login_import.get_query_id(), scopes_required[scope])
        self.assertListEqual(
            scopes_required["esi-markets.structure_markets.v1"],
            ["marketmanager_character", "marketmanager_corporation"],
        )
