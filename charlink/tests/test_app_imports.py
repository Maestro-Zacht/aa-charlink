from importlib import import_module
from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory

from charlink.app_imports import import_apps


class TestImportApps(TestCase):

    @patch('charlink.app_imports.import_module', wraps=import_module)
    @patch('charlink.app_imports._imported', False)
    def test_not_imported(self, mock_import_module):
        imported_apps = import_apps()
        self.assertTrue(mock_import_module.called)
        self.assertIn('add_character', imported_apps)
        self.assertIn('allianceauth.corputils', imported_apps)
        self.assertNotIn('allianceauth', imported_apps)
        self.assertNotIn('allianceauth.authentication', imported_apps)
        mock_import_module.assert_any_call('charlink.imports.allianceauth.authentication')

    @patch('charlink.app_imports.import_module', wraps=import_module)
    def test_imported(self, mock_import_module):
        import_apps()
        mock_import_module.reset_mock()
        imported_apps = import_apps()
        self.assertFalse(mock_import_module.called)
        self.assertIn('add_character', imported_apps)
        self.assertIn('allianceauth.corputils', imported_apps)
        self.assertNotIn('allianceauth', imported_apps)
        self.assertNotIn('allianceauth.authentication', imported_apps)

    def test_supported_apps_default(self):
        user = UserMainFactory()
        main_char = user.profile.main_character

        add_char = import_apps()['add_character']
        self.assertIsNone(add_char.imports[0].add_character(None, None))
        self.assertTrue(add_char['is_character_added'](main_char))


class TestLoginImport(TestCase):

    def test_get_query_id(self):
        login_import = import_apps()['add_character'].get('default')
        self.assertEqual(login_import.get_query_id(), 'add_character_default')

    def test_hash(self):
        login_import = import_apps()['add_character'].get('default')
        self.assertEqual(hash(login_import), hash('add_character_default'))


class TestAppImport(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_get_form_fields(self):
        app_import = import_apps()['add_character']
        form_fields = app_import.get_form_fields(self.user)
        self.assertEqual(len(form_fields), 1)
        self.assertIn('add_character_default', form_fields)

    def test_get_imports_with_perms(self):
        # TODO: test with multiple login imports
        app_import = import_apps()['add_character']
        imports = app_import.get_imports_with_perms(self.user)
        self.assertEqual(len(imports.imports), 1)

    def test_has_any_perms(self):
        app_import = import_apps()['add_character']
        self.assertTrue(app_import.has_any_perms(self.user))

    def test_get_ok(self):
        app_import = import_apps()['add_character']
        login_import = app_import.get('default')
        self.assertEqual(login_import.unique_id, 'default')

    def test_get_not_found(self):
        app_import = import_apps()['add_character']
        with self.assertRaises(KeyError):
            app_import.get('not_found')
