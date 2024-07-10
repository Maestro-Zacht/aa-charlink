from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.miningtaxes import _add_character_basic, _is_character_added_basic, _add_character_admin, _is_character_added_admin
from charlink.app_imports import import_apps

from miningtaxes.models import Character, AdminCharacter


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.character = cls.user.profile.main_character

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    @patch('miningtaxes.tasks.update_character.delay')
    def test_ok_basic(self, mock_update_character):
        mock_update_character.return_value = None

        token = self.user.token_set.first()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        _add_character_basic(request, token)

        mock_update_character.assert_called_once()
        self.assertTrue(_is_character_added_basic(self.character))

    @patch('miningtaxes.tasks.update_admin_character.delay')
    def test_ok_admin(self, mock_update_character):
        mock_update_character.return_value = None

        token = self.user.token_set.first()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        _add_character_admin(request, token)

        mock_update_character.assert_called_once()
        self.assertTrue(_is_character_added_admin(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.character = cls.user.profile.main_character

    def test_ok_basic(self):
        self.assertFalse(_is_character_added_basic(self.character))
        Character.objects.create(eve_character=self.character)
        self.assertTrue(_is_character_added_basic(self.character))

    def test_ok_admin(self):
        self.assertFalse(_is_character_added_admin(self.character))
        AdminCharacter.objects.create(eve_character=self.character)
        self.assertTrue(_is_character_added_admin(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user_basic = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.perm_user_admin = UserMainFactory(permissions=["miningtaxes.admin_access"])

    def test_ok_basic(self):
        login_import = import_apps()['miningtaxes'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user_basic))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))

    def test_ok_admin(self):
        login_import = import_apps()['miningtaxes'].get('admin')

        self.assertTrue(login_import.check_permissions(self.perm_user_admin))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user_basic = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.perm_user_admin = UserMainFactory(permissions=["miningtaxes.admin_access"])

    def test_ok_basic(self):
        login_import = import_apps()['miningtaxes'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user_basic)

    def test_ok_admin(self):
        login_import = import_apps()['miningtaxes'].get('admin')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user_admin)
