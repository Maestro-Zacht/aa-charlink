from importlib import import_module
from unittest.mock import patch

from django.test import TestCase

from allianceauth.tests.auth_utils import AuthUtils

from app_utils.testdata_factories import UserMainFactory

from charlink.app_imports import import_apps, get_duplicated_apps, get_failed_to_import, get_no_import
from charlink.imports.corptools import _corp_perms


class TestImportApps(TestCase):

    @patch('charlink.app_imports.import_module', wraps=import_module)
    @patch('charlink.app_imports._imported', False)
    @patch('charlink.app_imports._duplicated_apps', set())
    @patch('charlink.app_imports._supported_apps', {})
    def test_not_imported(self, mock_import_module):
        imported_apps = import_apps()
        failed = get_failed_to_import()
        no_import = get_no_import()
        duplicated = get_duplicated_apps()

        self.assertTrue(mock_import_module.called)
        self.assertIn('allianceauth.authentication', imported_apps)
        self.assertIn('allianceauth.corputils', imported_apps)
        self.assertIn('testauth.testapp', imported_apps)
        self.assertNotIn('fakeapp', imported_apps)
        self.assertIn('testauth.testapp.charlink_hook_invalid', failed)
        self.assertNotIn('fakeapp2', imported_apps)
        self.assertIn('testauth.testapp.charlink_hook_no_import', failed)
        self.assertNotIn('allianceauth', imported_apps)
        self.assertNotIn('allianceauth.eveonline', imported_apps)
        self.assertIn('testauth.testapp.charlink_hook_no_import', failed)
        mock_import_module.assert_any_call('charlink.imports.allianceauth.eveonline')

        self.assertSetEqual({'testauth.testapp_duplicate'}, duplicated)
        self.assertIn('charlink', no_import)

    @patch('charlink.app_imports.import_module', wraps=import_module)
    def test_imported(self, mock_import_module):
        import_apps()
        mock_import_module.reset_mock()
        imported_apps = import_apps()
        self.assertFalse(mock_import_module.called)
        self.assertIn('allianceauth.authentication', imported_apps)
        self.assertIn('allianceauth.corputils', imported_apps)
        self.assertIn('testauth.testapp', imported_apps)
        self.assertNotIn('allianceauth', imported_apps)
        self.assertNotIn('allianceauth.eveonline', imported_apps)

    def test_supported_apps_default(self):
        user = UserMainFactory()
        main_char = user.profile.main_character

        add_char = import_apps()['allianceauth.authentication']
        self.assertIsNone(add_char.imports[0].add_character(None, None))
        self.assertTrue(add_char.imports[0].is_character_added(main_char))
        self.assertTrue(add_char.imports[0].check_permissions(user))
        self.assertEqual(add_char.imports[0].get_users_with_perms().count(), 1)

    def test_ignore_duplicate_imports(self):
        imported_apps = import_apps()
        self.assertNotIn('testauth.testapp_duplicate', imported_apps)
        self.assertSetEqual({'testauth.testapp_duplicate'}, get_duplicated_apps())

    @patch('charlink.app_imports.import_module', wraps=import_module)
    @patch('charlink.app_imports._imported', False)
    @patch('charlink.app_imports._duplicated_apps', set())
    @patch('charlink.app_imports._supported_apps', {})
    def test_get_duplicated_apps_imports_apps(self, mock_import_module):
        get_duplicated_apps()
        self.assertTrue(mock_import_module.called)


class TestLoginImport(TestCase):

    def test_get_query_id(self):
        login_import = import_apps()['allianceauth.authentication'].get('default')
        self.assertEqual(login_import.get_query_id(), 'allianceauth.authentication_default')

    def test_hash(self):
        login_import = import_apps()['allianceauth.authentication'].get('default')
        self.assertEqual(hash(login_import), hash('allianceauth.authentication_default'))

    @patch('charlink.app_imports.utils.CHARLINK_IGNORE_APPS', {'marketmanager.corporation', 'corptools'})
    def test_is_ignored(self):
        marketmanager = import_apps()['marketmanager']
        corptools = import_apps()['corptools']

        corporation_import = marketmanager.get('corporation')
        character_import = marketmanager.get('character')

        self.assertTrue(corporation_import.is_ignored)
        self.assertFalse(character_import.is_ignored)

        for import_ in corptools.imports:
            self.assertTrue(import_.is_ignored)


class TestAppImport(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_get_form_fields(self):
        imported_apps = import_apps()
        user = AuthUtils.add_permissions_to_user_by_name(['corptools.view_characteraudit', "marketmanager.basic_market_browser", *_corp_perms], self.user)
        app_import = imported_apps['allianceauth.authentication']
        form_fields_auth = app_import.get_form_fields(user)
        self.assertEqual(len(form_fields_auth), 1)
        self.assertIn('allianceauth.authentication_default', form_fields_auth)

        marketmanager = imported_apps['marketmanager']
        form_fields_marketmanager = marketmanager.get_form_fields(user)
        self.assertEqual(len(form_fields_marketmanager), 2)
        self.assertIn('marketmanager_corporation', form_fields_marketmanager)
        self.assertIn('marketmanager_character', form_fields_marketmanager)

        corptools = imported_apps['corptools']
        form_fields_corptools = corptools.get_form_fields(user)
        self.assertEqual(len(form_fields_corptools), 2)
        self.assertIn('corptools_default', form_fields_corptools)
        self.assertIn('corptools_structures', form_fields_corptools)

    @patch('charlink.app_imports.utils.CHARLINK_IGNORE_APPS', {'marketmanager.corporation', 'corptools'})
    def test_get_form_fields_ignore(self):
        user = AuthUtils.add_permissions_to_user_by_name(['corptools.view_characteraudit', "marketmanager.basic_market_browser", *_corp_perms], self.user)
        app_import = import_apps()['allianceauth.authentication']
        form_fields = app_import.get_form_fields(user)
        self.assertEqual(len(form_fields), 1)
        self.assertIn('allianceauth.authentication_default', form_fields)

        marketmanager = import_apps()['marketmanager']
        form_fields = marketmanager.get_form_fields(user)
        self.assertEqual(len(form_fields), 1)
        self.assertIn('marketmanager_character', form_fields)
        self.assertNotIn('marketmanager_corporation', form_fields)

        corptools = import_apps()['corptools']
        form_fields = corptools.get_form_fields(user)
        self.assertEqual(len(form_fields), 0)

    def test_get_imports_with_perms(self):
        app_import = import_apps()['allianceauth.authentication']
        imports = app_import.get_imports_with_perms(self.user)
        self.assertEqual(len(imports.imports), 1)

        user_corp = UserMainFactory(permissions=_corp_perms)
        user_charaudit = UserMainFactory(permissions=['corptools.view_characteraudit'])
        user_both = UserMainFactory(permissions=['corptools.view_characteraudit', *_corp_perms])

        corptools_import = import_apps()['corptools']

        imports_corp = corptools_import.get_imports_with_perms(user_corp)
        self.assertEqual(len(imports_corp.imports), 1)
        self.assertEqual(imports_corp.imports[0].unique_id, 'structures')

        imports_charaudit = corptools_import.get_imports_with_perms(user_charaudit)
        self.assertEqual(len(imports_charaudit.imports), 1)
        self.assertEqual(imports_charaudit.imports[0].unique_id, 'default')

        imports_both = corptools_import.get_imports_with_perms(user_both)
        self.assertEqual(len(imports_both.imports), 2)

    @patch('charlink.app_imports.utils.CHARLINK_IGNORE_APPS', {'marketmanager.corporation', 'corptools'})
    def test_get_imports_with_perms_ignore(self):
        app_import = import_apps()['allianceauth.authentication']
        imports = app_import.get_imports_with_perms(self.user)
        self.assertEqual(len(imports.imports), 1)

        user_corp = UserMainFactory(permissions=_corp_perms)
        user_charaudit = UserMainFactory(permissions=['corptools.view_characteraudit'])
        user_both = UserMainFactory(permissions=['corptools.view_characteraudit', *_corp_perms])

        corptools_import = import_apps()['corptools']

        imports_corp = corptools_import.get_imports_with_perms(user_corp)
        self.assertEqual(len(imports_corp.imports), 0)

        imports_charaudit = corptools_import.get_imports_with_perms(user_charaudit)
        self.assertEqual(len(imports_charaudit.imports), 0)

        imports_both = corptools_import.get_imports_with_perms(user_both)
        self.assertEqual(len(imports_both.imports), 0)

        user_marketmanager = UserMainFactory(permissions=['marketmanager.basic_market_browser'])
        marketmanager_import = import_apps()['marketmanager']

        imports_marketmanager = marketmanager_import.get_imports_with_perms(user_marketmanager)
        self.assertEqual(len(imports_marketmanager.imports), 1)
        self.assertEqual(imports_marketmanager.imports[0].unique_id, 'character')

    def test_has_any_perms(self):
        app_import = import_apps()['allianceauth.authentication']
        self.assertTrue(app_import.has_any_perms(self.user))

    @patch('charlink.app_imports.utils.CHARLINK_IGNORE_APPS', {'marketmanager.corporation', 'corptools'})
    def test_has_any_perms_ignore(self):
        app_import = import_apps()['allianceauth.authentication']
        self.assertTrue(app_import.has_any_perms(self.user))

        user_marketmanager = UserMainFactory(permissions=['marketmanager.basic_market_browser'])
        marketmanager_import = import_apps()['marketmanager']
        self.assertTrue(marketmanager_import.has_any_perms(user_marketmanager))

        user_both = UserMainFactory(permissions=['corptools.view_characteraudit', *_corp_perms])
        corptools_import = import_apps()['corptools']
        self.assertFalse(corptools_import.has_any_perms(user_both))

    def test_get_ok(self):
        app_import = import_apps()['allianceauth.authentication']
        login_import = app_import.get('default')
        self.assertEqual(login_import.unique_id, 'default')

    def test_get_not_found(self):
        app_import = import_apps()['allianceauth.authentication']
        with self.assertRaises(KeyError):
            app_import.get('not_found')

    def test_validate_import(self):
        app_import = import_apps()['allianceauth.authentication']
        app_import.validate_import()

        app_import.app_label = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.app_label = 'allianceauth.authentication'

        tmp = app_import.imports
        app_import.imports = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports = []
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports = tmp

        app_import.validate_import()
        app_import.imports[0].unique_id = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].unique_id = 'default'

        app_import.imports[0].unique_id = 'invalid id'
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].unique_id = 'default'

        app_import.imports[0].add_character = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].add_character = lambda request, token: None

        app_import.imports[0].scopes = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].scopes = ['publicData']

        app_import.imports[0].check_permissions = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].check_permissions = lambda user: True

        tmp = app_import.imports[0].is_character_added
        app_import.imports[0].is_character_added = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].is_character_added = tmp

        tmp = app_import.imports[0].is_character_added_annotation
        app_import.imports[0].is_character_added_annotation = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].is_character_added_annotation = tmp

        tmp = app_import.imports[0].get_users_with_perms
        app_import.imports[0].get_users_with_perms = 1
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].get_users_with_perms = tmp

        app_import.imports.append(app_import.imports[0])
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports = [app_import.imports[0]]

        app_import.imports[0].app_label = 'different_app'
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.imports[0].app_label = 'allianceauth.authentication'

        app_import.app_label = 'different_app'
        with self.assertRaises(AssertionError):
            app_import.validate_import()
        app_import.app_label = 'allianceauth.authentication'
