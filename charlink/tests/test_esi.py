from django.test import TestCase

from esi.models import Scope, Token

from app_utils.testdata_factories import UserFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user, add_new_token


class TestScope(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.character = EveCharacterFactory()

    def test_token(self):
        add_character_to_user(self.user, self.character, scopes=['esi-fleets.read_fleet.v1'])
        token = Token.objects.get(character_id=self.character.character_id)
        self.assertEqual(token.scopes.count(), 1)
        self.assertEqual(len(token.scopes.values_list('pk', flat=True)), 1)

    def test_required_scopes(self):
        add_character_to_user(self.user, self.character, scopes=["esi-location.read_location.v1", "esi-location.read_ship_type.v1", "esi-location.read_online.v1"])
        tokens = Token.objects.all().require_scopes(["esi-location.read_location.v1", "esi-location.read_ship_type.v1"])
        self.assertEqual(len(tokens), 1)
