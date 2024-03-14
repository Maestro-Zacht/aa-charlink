from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.corptools import _add_character_charaudit, _is_character_added_charaudit, _corp_perms, _is_character_added_corp, _add_character_corp
from charlink.app_imports import import_apps


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['corptools.view_characteraudit', *_corp_perms])

    @patch('charlink.imports.corptools.update_character.apply_async')
    def test_ok_charaudit(self, mock_update_character):
        mock_update_character.return_value = None

        token = self.user.token_set.first()

        _add_character_charaudit(token)

        mock_update_character.assert_called_once_with(args=[token.character_id], priority=6)
        self.assertTrue(_is_character_added_charaudit(self.user.profile.main_character))

    @patch('charlink.imports.corptools.update_all_corps.apply_async')
    def test_ok_corp(self, mock_update_all_corps):
        mock_update_all_corps.return_value = None

        token = self.user.token_set.first()

        _add_character_corp(token)

        self.assertTrue(_is_character_added_corp(self.user.profile.main_character))
        self.assertTrue(mock_update_all_corps.called)


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.character = cls.user.profile.main_character

    @patch('charlink.imports.corptools.update_character.apply_async')
    def test_ok_charaudit(self, mock_update_character):
        mock_update_character.return_value = None

        self.assertFalse(_is_character_added_charaudit(self.character))
        _add_character_charaudit(self.user.token_set.first())
        self.assertTrue(_is_character_added_charaudit(self.character))

    @patch('charlink.imports.corptools.update_all_corps.apply_async')
    def test_ok_corp(self, mock_update_all_corps):
        mock_update_all_corps.return_value = None

        self.assertFalse(_is_character_added_corp(self.character))
        _add_character_corp(self.user.token_set.first())
        self.assertTrue(_is_character_added_corp(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.charaudit_user = UserMainFactory(permissions=['corptools.view_characteraudit'])
        cls.corp_user = UserMainFactory(permissions=_corp_perms)

    def test_ok_charaudit(self):
        login_import = import_apps()['corptools'].get('default')

        self.assertFalse(login_import.check_permissions(self.no_perm_user))
        self.assertTrue(login_import.check_permissions(self.charaudit_user))

    def test_ok_corp(self):
        login_import = import_apps()['corptools'].get('structures')

        self.assertFalse(login_import.check_permissions(self.no_perm_user))
        self.assertTrue(login_import.check_permissions(self.corp_user))
        self.assertFalse(login_import.check_permissions(self.charaudit_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        UserMainFactory.create_batch(4)
        UserMainFactory.create_batch(3, permissions=['corptools.view_characteraudit'])
        UserMainFactory.create_batch(5, permissions=_corp_perms)

    def test_ok_charaudit(self):
        login_import = import_apps()['corptools'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 3)

    def test_ok_corp(self):
        login_import = import_apps()['corptools'].get('structures')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 5)
