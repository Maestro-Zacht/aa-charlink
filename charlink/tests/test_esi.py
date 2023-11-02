from django.test import TestCase
from django.db.models import Exists, OuterRef

from esi.models import Token
from esi.managers import _process_scopes

from app_utils.testdata_factories import UserFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user

from allianceauth.eveonline.models import EveCharacter


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
        scopes = ["esi-location.read_location.v1", "esi-location.read_ship_type.v1", "esi-location.read_online.v1"]
        add_character_to_user(self.user, self.character, scopes=scopes)
        processed_scopes = _process_scopes(scopes)
        from esi.models import Scope
        scope_pks = Scope.objects.filter(name__in=scopes).values_list('pk', flat=True)
        self.assertEqual(len(processed_scopes), len(scope_pks))

    def test_annotation(self):
        scopes = ["esi-location.read_location.v1", "esi-location.read_ship_type.v1", "esi-location.read_online.v1"]
        add_character_to_user(self.user, self.character, scopes=scopes)
        annotation = Exists(
            Token.objects.all()
            .filter(character_id=OuterRef('character_id'))
            .require_scopes(scopes)
        )
        chars = EveCharacter.objects.annotate(has_scopes=annotation)
        self.assertEqual(chars.count(), 1)
        char = chars.first()
        self.assertTrue(char.has_scopes)
