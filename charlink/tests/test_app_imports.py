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
        self.assertIsNone(add_char['add_character'](None, None))
        self.assertTrue(add_char['is_character_added'](main_char))