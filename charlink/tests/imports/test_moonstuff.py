from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.moonstuff import _add_character, _is_character_added
from charlink.app_imports import import_apps


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['moonstuff.add_trackingcharacter'])

    @patch('charlink.imports.moonstuff.import_extraction_data.delay')
    def test_ok(self, mock_import_extraction_data):
        mock_import_extraction_data.return_value = None

        token = self.user.token_set.first()

        _add_character(token)

        self.assertTrue(_is_character_added(self.user.profile.main_character))

        _add_character(token)

        mock_import_extraction_data.assert_called_once()
        self.assertTrue(_is_character_added(self.user.profile.main_character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['moonstuff.add_trackingcharacter'])
        cls.character = cls.user.profile.main_character

    @patch('charlink.imports.moonstuff.import_extraction_data.delay')
    def test_ok(self, mock_import_extraction_data):
        mock_import_extraction_data.return_value = None

        self.assertFalse(_is_character_added(self.character))

        token = self.user.token_set.first()

        _add_character(token)

        self.assertTrue(_is_character_added(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["moonstuff.add_trackingcharacter"])

    def test_ok(self):
        login_import = import_apps()['moonstuff'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["moonstuff.add_trackingcharacter"])

    def test_ok(self):
        login_import = import_apps()['moonstuff'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user)
