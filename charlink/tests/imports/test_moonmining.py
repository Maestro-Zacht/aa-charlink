from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory

from charlink.imports.moonmining import _add_character, _is_character_added
from charlink.app_imports import import_apps


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=[
            "moonmining.add_refinery_owner",
            "moonmining.basic_access"
        ])
        cls.character = cls.user.profile.main_character

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    @patch('moonmining.tasks.update_owner.delay')
    def test_ok(self, mock_update_owner):
        mock_update_owner.return_value = None

        token = self.user.token_set.first()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        _add_character(request, token)

        mock_update_owner.assert_called_once()
        self.assertTrue(_is_character_added(self.character))

    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch('moonmining.tasks.update_owner.delay')
    def test_missing_corporation(self, mock_update_owner, mock_create_corporation):
        mock_update_owner.return_value = None

        self.character.corporation.delete()

        token = self.user.token_set.first()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        _add_character(request, token)

        mock_update_owner.assert_called_once()
        mock_create_corporation.assert_called_once()
        self.assertTrue(_is_character_added(self.character))

    @patch('moonmining.tasks.update_owner.delay')
    @patch('charlink.imports.moonmining.MOONMINING_ADMIN_NOTIFICATIONS_ENABLED', False)
    @patch('charlink.imports.moonmining.notify_admins')
    def test_no_admin_notification(self, mock_notify_admins, mock_update_owner):
        mock_update_owner.return_value = None
        mock_notify_admins.return_value = None

        token = self.user.token_set.first()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        _add_character(request, token)

        self.assertFalse(mock_notify_admins.called)
        mock_update_owner.assert_called_once()
        self.assertTrue(_is_character_added(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=[
            "moonmining.add_refinery_owner",
            "moonmining.basic_access"
        ])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    @patch('moonmining.tasks.update_owner.delay')
    def test_ok(self, mock_update_owner):
        mock_update_owner.return_value = None

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages

        self.assertFalse(_is_character_added(self.character))
        _add_character(request, self.token)
        self.assertTrue(_is_character_added(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["moonmining.add_refinery_owner", "moonmining.basic_access"])

    def test_ok(self):
        login_import = import_apps()['moonmining'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["moonmining.add_refinery_owner", "moonmining.basic_access"])

    def test_ok(self):
        login_import = import_apps()['moonmining'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user)
