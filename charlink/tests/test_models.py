from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User

from app_utils.testdata_factories import UserMainFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user, add_new_token

from charlink.imports.allianceauth.authentication import app_import as auth_import
from charlink.imports.corptools import app_import as corptools_import
from charlink.app_imports import import_apps
from charlink.models import AppSettings, BaseFilter, ComplianceFilter

from corptools.models import CharacterAudit

from esi.models import Token


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestAppSettings(TestCase):

    def test_str_method(self):
        import_apps()

        app_setting = AppSettings.objects.get(app_name='allianceauth.authentication_default')

        self.assertEqual(str(app_setting), str(auth_import.get('default').field_label))


class BaseFilterTestImpl(BaseFilter):
    class Meta:
        app_label = 'charlink'


class TestBaseFilter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.base_filter = BaseFilterTestImpl(name="test", description="test description")

    def test_str_method(self):
        self.assertEqual(str(self.base_filter), "test: test description")

    def test_process_filter_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.base_filter.process_filter(None)

    def test_audit_filter_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.base_filter.audit_filter(None)


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestComplianceFilter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(main_character__scopes=corptools_import.get('default').scopes)
        cls.compliance_filter = ComplianceFilter.objects.create(name="compliance test", description="compliance description")
        import_apps()
        cls.compliance_filter.selected_apps.add(AppSettings.objects.get(app_name='allianceauth.authentication_default'))

    @patch('charlink.models.ComplianceFilter.audit_filter')
    def test_process_filter(self, mock_audit_filter):
        mock_audit_filter.return_value = {self.user.pk: {'check': True, 'message': 'All good'}}

        res = self.compliance_filter.process_filter(self.user)

        mock_audit_filter.assert_called_once()
        self.assertTrue(res)

    def test_audit_filter_simple(self):
        res = self.compliance_filter.audit_filter(User.objects.filter(pk=self.user.pk))
        self.assertDictEqual(res, {self.user.pk: {'check': True, 'message': 'Meets requirements'}})

    @patch('charlink.imports.corptools.update_character.apply_async')
    def test_audit_filter_with_2_apps(self, mock_update_character):
        mock_update_character.return_value = None

        character = EveCharacterFactory()
        add_character_to_user(self.user, character)

        self.compliance_filter.selected_apps.add(AppSettings.objects.get(app_name='corptools_default'))

        res = self.compliance_filter.audit_filter(User.objects.filter(pk=self.user.pk))
        self.assertDictEqual(res, {self.user.pk: {'check': False, 'message': 'Does not meet requirements'}})

        token2 = add_new_token(self.user, character, scopes=corptools_import.get('default').scopes)
        corptools_import.get('default').add_character(None, token2)

        res = self.compliance_filter.audit_filter(User.objects.filter(pk=self.user.pk))
        self.assertDictEqual(res, {self.user.pk: {'check': False, 'message': 'Does not meet requirements'}})

        main_token = Token.objects.get(user=self.user, character_id=self.user.profile.main_character.character_id)
        corptools_import.get('default').add_character(None, main_token)

        CharacterAudit.objects.update(active=True)

        res = self.compliance_filter.audit_filter(User.objects.filter(pk=self.user.pk))
        self.assertDictEqual(res, {self.user.pk: {'check': True, 'message': 'Meets requirements'}})

    def test_audit_filter_removed_app(self):
        new_as = AppSettings.objects.create(app_name='non_existent_app')
        self.compliance_filter.selected_apps.add(new_as)

        res = self.compliance_filter.audit_filter(User.objects.filter(pk=self.user.pk))
        self.assertFalse(res[self.user.pk]['check'])
        self.assertEqual(res[self.user.pk]['message'], '')
