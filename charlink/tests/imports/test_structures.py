from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user

from charlink.imports.structures import add_character, is_character_added

from structures.models import Webhook, Owner


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["structures.add_structure_owner"])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()
        cls.factory = RequestFactory()

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_ok(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_missing_corp(self, mock_update_all_for_owner, mock_messages_plus_info, mock_create_corporation):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        self.character.corporation.delete()

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        self.assertTrue(mock_update_all_for_owner.called)
        self.assertTrue(mock_messages_plus_info.called)
        self.assertTrue(mock_create_corporation.called)

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_already_added(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        add_character(request, self.token)
        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_default_webhooks(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        Webhook.objects.create(is_default=True, name="test", url="https://discordapp.com/api/webhooks/123456/abcdef")

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)
        self.assertEqual(Owner.objects.first().webhooks.count(), 1)

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    @patch('charlink.imports.structures.STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED', False)
    def test_no_admin_notifications(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_second_owner(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

        character2 = EveCharacterFactory(corporation=self.character.corporation)
        add_character_to_user(character2, self.user)

        add_character(request, self.user.token_set.get(character_id=character2.character_id))

        self.assertTrue(is_character_added(character2))
        self.assertEqual(Owner.objects.first().characters_count(), 2)
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    @patch('charlink.imports.structures.STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED', False)
    def test_second_owner_no_admin_notifications(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)

        character2 = EveCharacterFactory(corporation=self.character.corporation)
        add_character_to_user(character2, self.user)

        add_character(request, self.user.token_set.get(character_id=character2.character_id))

        self.assertTrue(is_character_added(character2))
        self.assertEqual(Owner.objects.first().characters_count(), 2)
        mock_update_all_for_owner.assert_called_once()
        self.assertTrue(mock_messages_plus_info.called)


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["structures.add_structure_owner"])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()
        cls.factory = RequestFactory()

    @patch('app_utils.messages.messages_plus.info')
    @patch("structures.tasks.update_all_for_owner.delay")
    def test_ok(self, mock_update_all_for_owner, mock_messages_plus_info):
        mock_update_all_for_owner.return_value = None
        mock_messages_plus_info.return_value = None

        request = self.factory.get("/charlink/login/")
        request.user = self.user

        self.assertFalse(is_character_added(self.character))

        add_character(request, self.token)

        self.assertTrue(is_character_added(self.character))
