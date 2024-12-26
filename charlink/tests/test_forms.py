from unittest.mock import patch

from django.test import TestCase

from allianceauth.tests.auth_utils import AuthUtils

from app_utils.testdata_factories import UserMainFactory

from charlink.forms import LinkForm


class TestLinkForm(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_init_no_perms(self):
        form = LinkForm(self.user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertNotIn('allianceauth.corputils_default', form.fields)

    def test_init_with_perms(self):
        user = AuthUtils.add_permissions_to_user_by_name(['corputils.add_corpstats', "marketmanager.basic_market_browser"], self.user)
        form = LinkForm(user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertIn('allianceauth.corputils_default', form.fields)
        self.assertIn('marketmanager_corporation', form.fields)
        self.assertIn('marketmanager_character', form.fields)

    @patch('charlink.forms.CHARLINK_IGNORE_APPS', {'allianceauth.corputils', 'marketmanager.corporation'})
    @patch('charlink.app_imports.utils.CHARLINK_IGNORE_APPS', {'allianceauth.corputils', 'marketmanager.corporation'})
    def test_init_with_perms_ignore(self):
        user = AuthUtils.add_permissions_to_user_by_name(['corputils.add_corpstats', "marketmanager.basic_market_browser"], self.user)
        form = LinkForm(user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertNotIn('allianceauth.corputils_default', form.fields)
        self.assertNotIn('marketmanager_corporation', form.fields)
        self.assertIn('marketmanager_character', form.fields)
