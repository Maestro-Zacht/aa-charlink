from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.corptools import _add_character_charaudit, _is_character_added_charaudit
from charlink.app_imports import import_apps


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.factory = RequestFactory()

    @patch('charlink.imports.corptools.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        request = self.factory.get('/charlink/login/')
        token = self.user.token_set.first()

        _add_character_charaudit(request, token)

        mock_update_character.assert_called_once_with(args=[token.character_id], priority=6)
        self.assertTrue(_is_character_added_charaudit(self.user.profile.main_character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('charlink.imports.corptools.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        self.assertFalse(_is_character_added_charaudit(self.character))
        _add_character_charaudit(self.factory.get('/charlink/login/'), self.user.token_set.first())
        self.assertTrue(_is_character_added_charaudit(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_ok(self):
        login_import = import_apps()['corptools'].get('default')

        self.assertTrue(login_import.check_permissions(self.user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        UserMainFactory.create_batch(3)

    def test_ok(self):
        login_import = import_apps()['corptools'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 3)
