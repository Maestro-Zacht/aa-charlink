from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.aa_contacts import (
    _alliance_login,
    _corporation_login,
    _alliance_users_with_perms,
    _corporation_users_with_perms,
    _alliance_check_perms,
    _corporation_check_perms,
    _alliance_is_character_added,
    _corporation_is_character_added
)

from aa_contacts.models import AllianceToken, CorporationToken


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()

    @patch("charlink.imports.aa_contacts.update_alliance_contacts.delay")
    def test_alliance_login_ok(self, mock_update_alliance_contacts):
        mock_update_alliance_contacts.return_value = None

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        _alliance_login(request, self.token)

        self.assertTrue(AllianceToken.objects.filter(alliance=self.character.alliance).exists())
        self.assertTrue(mock_update_alliance_contacts.called)

    @patch("charlink.imports.aa_contacts.update_alliance_contacts.delay")
    def test_alliance_login_missing_alliance(self, mock_update_alliance_contacts):
        mock_update_alliance_contacts.return_value = None

        self.character.alliance.delete()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        _alliance_login(request, self.token)

        self.assertTrue(AllianceToken.objects.filter(alliance=self.character.alliance).exists())
        self.assertTrue(mock_update_alliance_contacts.called)

    @patch("charlink.imports.aa_contacts.update_corporation_contacts.delay")
    def test_character_not_in_alliance(self, mock_update_corporation_contacts):
        mock_update_corporation_contacts.return_value = None

        self.character.alliance.delete()
        self.character.alliance_id = None
        self.character.save()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        with self.assertRaises(AssertionError):
            _alliance_login(request, self.token)

        self.assertFalse(AllianceToken.objects.filter(alliance=self.character.alliance).exists())
        self.assertFalse(mock_update_corporation_contacts.called)

    @patch("charlink.imports.aa_contacts.update_corporation_contacts.delay")
    def test_alliance_already_tracked(self, mock_update_corporation_contacts):
        mock_update_corporation_contacts.return_value = None

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        AllianceToken.objects.create(alliance=self.character.alliance, token=self.token)
        with self.assertRaises(AssertionError):
            _alliance_login(request, self.token)

        self.assertTrue(AllianceToken.objects.filter(alliance=self.character.alliance).exists())
        self.assertFalse(mock_update_corporation_contacts.called)

    @patch("charlink.imports.aa_contacts.update_corporation_contacts.delay")
    def test_corporation_login_ok(self, mock_update_corporation_contacts):
        mock_update_corporation_contacts.return_value = None

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        _corporation_login(request, self.token)

        self.assertTrue(CorporationToken.objects.filter(corporation=self.character.corporation).exists())
        self.assertTrue(mock_update_corporation_contacts.called)

    @patch("charlink.imports.aa_contacts.update_corporation_contacts.delay")
    def test_corporation_login_missing_corporation(self, mock_update_corporation_contacts):
        mock_update_corporation_contacts.return_value = None

        self.character.corporation.delete()

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        _corporation_login(request, self.token)

        self.assertTrue(CorporationToken.objects.filter(corporation=self.character.corporation).exists())
        self.assertTrue(mock_update_corporation_contacts.called)

    @patch("charlink.imports.aa_contacts.update_corporation_contacts.delay")
    def test_corporation_already_tracked(self, mock_update_corporation_contacts):
        mock_update_corporation_contacts.return_value = None

        request = self.factory.get('/charlink/login/')
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        request._messages = messages
        request.user = self.user

        CorporationToken.objects.create(corporation=self.character.corporation, token=self.token)
        with self.assertRaises(AssertionError):
            _corporation_login(request, self.token)

        self.assertTrue(CorporationToken.objects.filter(corporation=self.character.corporation).exists())
        self.assertFalse(mock_update_corporation_contacts.called)


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_no_perm = UserMainFactory()
        cls.user_alliance_perm = UserMainFactory(permissions=["aa_contacts.manage_alliance_contacts"])
        cls.user_corporation_perm = UserMainFactory(permissions=["aa_contacts.manage_corporation_contacts"])

    def test_alliance_users_with_perms(self):
        users = _alliance_users_with_perms()

        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.user_alliance_perm)

    def test_corporation_users_with_perms(self):
        users = _corporation_users_with_perms()

        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.user_corporation_perm)


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_no_perm = UserMainFactory()
        cls.user_alliance_perm = UserMainFactory(permissions=["aa_contacts.manage_alliance_contacts"])
        cls.user_corporation_perm = UserMainFactory(permissions=["aa_contacts.manage_corporation_contacts"])

    def test_alliance_check_perms(self):
        self.assertTrue(_alliance_check_perms(self.user_alliance_perm))
        self.assertFalse(_alliance_check_perms(self.user_no_perm))

    def test_corporation_check_perms(self):
        self.assertTrue(_corporation_check_perms(self.user_corporation_perm))
        self.assertFalse(_corporation_check_perms(self.user_no_perm))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["aa_contacts.manage_alliance_contacts"])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()

    def test_alliance_ok(self):
        self.assertFalse(_alliance_is_character_added(self.character))
        AllianceToken.objects.create(alliance=self.character.alliance, token=self.token)
        self.assertTrue(_alliance_is_character_added(self.character))

    def test_corporation_ok(self):
        self.assertFalse(_corporation_is_character_added(self.character))
        CorporationToken.objects.create(corporation=self.character.corporation, token=self.token)
        self.assertTrue(_corporation_is_character_added(self.character))
