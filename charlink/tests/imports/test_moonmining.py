from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory

from charlink.imports.moonmining import add_character, is_character_added


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=[
            "moonmining.add_refinery_owner",
            "moonmining.basic_access"
        ])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('app_utils.messages.messages_plus.success')
    @patch('moonmining.tasks.update_owner.delay')
    def test_ok(self, mock_update_owner, mock_messages_plus_success):
        mock_update_owner.return_value = None
        mock_messages_plus_success.return_value = None

        request = self.factory.get('/charlink/login/')
        request.user = self.user
        token = self.user.token_set.first()

        add_character(request, token)

        mock_messages_plus_success.assert_called_once()
        mock_update_owner.assert_called_once()
        self.assertTrue(is_character_added(self.character))

    @patch('app_utils.messages.messages_plus.success')
    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch('moonmining.tasks.update_owner.delay')
    def test_missing_corporation(self, mock_update_owner, mock_create_corporation, mock_messages_plus_success):
        mock_update_owner.return_value = None
        mock_messages_plus_success.return_value = None

        self.character.corporation.delete()

        request = self.factory.get('/charlink/login/')
        request.user = self.user
        token = self.user.token_set.first()

        add_character(request, token)

        mock_messages_plus_success.assert_called_once()
        mock_update_owner.assert_called_once()
        mock_create_corporation.assert_called_once()
        self.assertTrue(is_character_added(self.character))

    @patch('app_utils.messages.messages_plus.success')
    @patch('moonmining.tasks.update_owner.delay')
    @patch('charlink.imports.moonmining.MOONMINING_ADMIN_NOTIFICATIONS_ENABLED', True)
    @patch('charlink.imports.moonmining.notify_admins')
    def test_admin_notification(self, mock_notify_admins, mock_update_owner, mock_messages_plus_success):
        mock_update_owner.return_value = None
        mock_notify_admins.return_value = None
        mock_messages_plus_success.return_value = None

        request = self.factory.get('/charlink/login/')
        request.user = self.user
        token = self.user.token_set.first()

        add_character(request, token)

        mock_messages_plus_success.assert_called_once()
        mock_notify_admins.assert_called_once()
        mock_update_owner.assert_called_once()
        self.assertTrue(is_character_added(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=[
            "moonmining.add_refinery_owner",
            "moonmining.basic_access"
        ])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()
        cls.factory = RequestFactory()

    @patch('app_utils.messages.messages_plus.success')
    @patch('moonmining.tasks.update_owner.delay')
    def test_ok(self, mock_update_owner, mock_messages_plus_success):
        mock_update_owner.return_value = None
        mock_messages_plus_success.return_value = None

        self.assertFalse(is_character_added(self.character))
        request = self.factory.get('/charlink/login/')
        request.user = self.user
        add_character(request, self.token)
        self.assertTrue(is_character_added(self.character))
