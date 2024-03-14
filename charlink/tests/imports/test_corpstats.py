from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user

from charlink.imports.corpstats import _add_character, _is_character_added
from charlink.app_imports import import_apps

from corpstats.models import CorpStat


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['corpstats.add_corpstat'])
        cls.token = cls.user.token_set.first()

    @patch('corpstats.models.CorpStat.update')
    def test_ok(self, mock_update):
        mock_update.return_value = None

        _add_character(self.token)

        self.assertTrue(mock_update.called)
        self.assertTrue(_is_character_added(self.user.profile.main_character))

    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch('corpstats.models.CorpStat.update')
    def test_corp_missing(self, mock_update, mock_create_corporation):
        mock_update.return_value = None
        character = self.user.profile.main_character

        character.corporation.delete()

        _add_character(self.token)

        self.assertTrue(mock_update.called)
        self.assertTrue(mock_create_corporation.called)
        self.assertTrue(_is_character_added(self.user.profile.main_character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['corputils.add_corpstats'])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()
        CorpStat.objects.create(token=cls.token, corp=cls.character.corporation)

    def test_ok(self):
        self.assertTrue(_is_character_added(self.character))

        newchar = EveCharacterFactory()
        add_character_to_user(self.user, newchar)

        self.assertFalse(_is_character_added(newchar))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.perm_user = UserMainFactory(permissions=['corpstats.add_corpstat'])
        cls.no_perm_user = UserMainFactory()

    def test_ok(self):
        login_import = import_apps()['corpstats'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.perm_user = UserMainFactory(permissions=['corpstats.add_corpstat'])
        cls.no_perm_user = UserMainFactory()

    def test_ok(self):
        login_import = import_apps()['corpstats'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user)
