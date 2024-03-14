from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user

from charlink.imports.structures import _add_character, _is_character_added
from charlink.app_imports import import_apps

from structures.models import Webhook, Owner


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["structures.add_structure_owner"])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()

    @patch("structures.tasks.update_all_for_owner.delay")
    def test_ok(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()

    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_missing_corp(self, mock_update_all_for_owner, mock_create_corporation):
        mock_update_all_for_owner.return_value = None

        self.character.corporation.delete()

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        self.assertTrue(mock_update_all_for_owner.called)
        self.assertTrue(mock_create_corporation.called)

    @patch("structures.tasks.update_all_for_owner.delay")
    def test_already_added(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        _add_character(self.token)
        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        self.assertTrue(mock_update_all_for_owner.called)

    @patch("structures.tasks.update_all_for_owner.delay")
    def test_default_webhooks(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        Webhook.objects.create(is_default=True, name="test", url="https://discordapp.com/api/webhooks/123456/abcdef")

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertEqual(Owner.objects.first().webhooks.count(), 1)

    @patch("structures.tasks.update_all_for_owner.delay")
    @patch('charlink.imports.structures.STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED', False)
    def test_no_admin_notifications(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()

    @patch("structures.tasks.update_all_for_owner.delay")
    def test_second_owner(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()

        character2 = EveCharacterFactory(corporation=self.character.corporation)
        add_character_to_user(self.user, character2)

        _add_character(self.user.token_set.get(character_id=character2.character_id))

        self.assertTrue(_is_character_added(character2))
        self.assertEqual(Owner.objects.first().characters_count(), 2)
        mock_update_all_for_owner.assert_called_once()

    @patch("structures.tasks.update_all_for_owner.delay")
    @patch('charlink.imports.structures.STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED', False)
    def test_second_owner_no_admin_notifications(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()

        character2 = EveCharacterFactory(corporation=self.character.corporation)
        add_character_to_user(self.user, character2)

        _add_character(self.user.token_set.get(character_id=character2.character_id))

        self.assertTrue(_is_character_added(character2))
        self.assertEqual(Owner.objects.first().characters_count(), 2)
        mock_update_all_for_owner.assert_called_once()


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["structures.add_structure_owner"])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()

    @patch("structures.tasks.update_all_for_owner.delay")
    def test_ok(self, mock_update_all_for_owner):
        mock_update_all_for_owner.return_value = None

        self.assertFalse(_is_character_added(self.character))

        _add_character(self.token)

        self.assertTrue(_is_character_added(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["structures.add_structure_owner"])

    def test_ok(self):
        login_import = import_apps()['structures'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["structures.add_structure_owner"])

    def test_ok(self):
        login_import = import_apps()['structures'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user)
