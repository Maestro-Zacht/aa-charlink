from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory

from charlink.imports.moonstuff import _add_character, _is_character_added


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['moonstuff.add_trackingcharacter'])
        cls.factory = RequestFactory()

    @patch('charlink.imports.moonstuff.import_extraction_data.delay')
    def test_ok(self, mock_import_extraction_data):
        mock_import_extraction_data.return_value = None

        request = self.factory.get('/charlink/login/')
        token = self.user.token_set.first()

        _add_character(request, token)

        self.assertTrue(_is_character_added(self.user.profile.main_character))

        _add_character(request, token)

        mock_import_extraction_data.assert_called_once()
        self.assertTrue(_is_character_added(self.user.profile.main_character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['moonstuff.add_trackingcharacter'])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('charlink.imports.moonstuff.import_extraction_data.delay')
    def test_ok(self, mock_import_extraction_data):
        mock_import_extraction_data.return_value = None

        self.assertFalse(_is_character_added(self.character))

        request = self.factory.get('/charlink/login/')
        token = self.user.token_set.first()

        _add_character(request, token)

        self.assertTrue(_is_character_added(self.character))
