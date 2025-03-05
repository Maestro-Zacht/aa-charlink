from unittest.mock import patch

from django.test import TestCase
from django.db.models import Q

from allianceauth.tests.auth_utils import AuthUtils

from app_utils.testdata_factories import UserMainFactory

from charlink.forms import LinkForm
from charlink.app_imports import import_apps
from charlink.models import AppSettings


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestLinkForm(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_init_no_perms(self):
        import_apps()
        form = LinkForm(self.user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertNotIn('allianceauth.corputils_default', form.fields)

    def test_init_with_perms(self):
        import_apps()
        user = AuthUtils.add_permissions_to_user_by_name(['corputils.add_corpstats', "marketmanager.basic_market_browser"], self.user)
        form = LinkForm(user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertIn('allianceauth.corputils_default', form.fields)
        self.assertIn('marketmanager_corporation', form.fields)
        self.assertIn('marketmanager_character', form.fields)

    def test_init_with_perms_ignore(self):
        import_apps()
        AppSettings.objects.filter(
            Q(app_name='allianceauth.corputils_default') | Q(app_name='marketmanager_corporation')
        ).update(ignored=True)

        user = AuthUtils.add_permissions_to_user_by_name(['corputils.add_corpstats', "marketmanager.basic_market_browser"], self.user)
        form = LinkForm(user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertNotIn('allianceauth.corputils_default', form.fields)
        self.assertNotIn('marketmanager_corporation', form.fields)
        self.assertIn('marketmanager_character', form.fields)
