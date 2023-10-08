from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user

from charlink.imports.corpstats import add_character, is_character_added

from corpstats.models import CorpStat


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['corpstats.add_corpstat'])
        cls.token = cls.user.token_set.first()
        cls.factory = RequestFactory()

    @patch('corpstats.models.CorpStat.update')
    def test_ok(self, mock_update):
        mock_update.return_value = None

        request = self.factory.get('/charlink/login/')

        add_character(request, self.token)

        self.assertTrue(mock_update.called)
        self.assertTrue(is_character_added(self.user.profile.main_character))

    @patch('allianceauth.eveonline.managers.EveCorporationManager.create_corporation', wraps=lambda corp_id: EveCorporationInfoFactory(corporation_id=corp_id))
    @patch('corpstats.models.CorpStat.update')
    def test_corp_missing(self, mock_update, mock_create_corporation):
        mock_update.return_value = None
        character = self.user.profile.main_character

        request = self.factory.get('/charlink/login/')
        character.corporation.delete()

        add_character(request, self.token)

        self.assertTrue(mock_update.called)
        self.assertTrue(mock_create_corporation.called)
        self.assertTrue(is_character_added(self.user.profile.main_character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['corputils.add_corpstats'])
        cls.character = cls.user.profile.main_character
        cls.token = cls.user.token_set.first()
        CorpStat.objects.create(token=cls.token, corp=cls.character.corporation)

    def test_ok(self):
        self.assertTrue(is_character_added(self.character))

        newchar = EveCharacterFactory()
        add_character_to_user(self.user, newchar)

        self.assertFalse(is_character_added(newchar))
