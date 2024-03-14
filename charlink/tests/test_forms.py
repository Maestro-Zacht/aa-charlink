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
        self.user = AuthUtils.add_permission_to_user_by_name('corputils.add_corpstats', self.user)
        form = LinkForm(self.user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertIn('allianceauth.corputils_default', form.fields)

    @patch('charlink.forms.CHARLINK_IGNORE_APPS', {'allianceauth.corputils'})
    def test_init_with_perms_ignore(self):
        self.user = AuthUtils.add_permission_to_user_by_name('corputils.add_corpstats', self.user)
        form = LinkForm(self.user)
        self.assertIn('allianceauth.authentication_default', form.fields)
        self.assertNotIn('allianceauth.corputils_default', form.fields)
