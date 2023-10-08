from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.miningtaxes import add_character, is_character_added


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('miningtaxes.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        request = self.factory.get('/charlink/login/')
        token = self.user.token_set.first()

        add_character(request, token)

        mock_update_character.assert_called_once()
        self.assertTrue(is_character_added(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["miningtaxes.basic_access"])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('miningtaxes.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        self.assertFalse(is_character_added(self.character))
        add_character(self.factory.get('/charlink/login/'), self.user.token_set.first())
        self.assertTrue(is_character_added(self.character))
