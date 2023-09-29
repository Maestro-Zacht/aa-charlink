from django.test import TestCase

from allianceauth.tests.auth_utils import AuthUtils

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import create_state

from charlink.utils import get_visible_corps


class TestGetVisibleCorps(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.superuser = UserMainFactory(is_superuser=True)

        cls.main_char = cls.user.profile.main_character

        cls.corporation = cls.user.profile.main_character.corporation
        cls.alliance = cls.corporation.alliance
        cls.state = cls.user.profile.state

        cls.corporation2 = EveCorporationInfoFactory(create_alliance=False)
        cls.corporation2.alliance = cls.alliance
        cls.corporation2.save()
        char = EveCharacterFactory(corporation=cls.corporation2)
        UserMainFactory(main_character__character=char)

        cls.corporation3 = EveCorporationInfoFactory()
        cls.alliance2 = cls.corporation3.alliance
        cls.state.member_alliances.add(cls.alliance2)
        char = EveCharacterFactory(corporation=cls.corporation3)
        UserMainFactory(main_character__character=char)

        cls.corporation_empty = EveCorporationInfoFactory(alliance=cls.alliance2)

        cls.corporation_superuser = cls.superuser.profile.main_character.corporation
        cls.alliance_superuser = cls.corporation2.alliance
        cls.state_superuser = create_state(1000, member_alliances=[cls.alliance_superuser])

    def test_superuser(self):
        corps = get_visible_corps(self.superuser)
        self.assertQuerysetEqual(
            corps,
            [
                self.corporation,
                self.corporation_superuser,
                self.corporation2,
                self.corporation3,
            ],
            ordered=False
        )

    def test_corp_access(self):
        AuthUtils.add_permission_to_user_by_name('charlink.view_corp', self.user)
        corps = get_visible_corps(self.user)
        self.assertQuerysetEqual(
            corps,
            [
                self.corporation,
            ],
            ordered=False
        )

    def test_alliance_access(self):
        AuthUtils.add_permission_to_user_by_name('charlink.view_alliance', self.user)
        corps = get_visible_corps(self.user)
        self.assertQuerysetEqual(
            corps,
            [
                self.corporation,
                self.corporation2,
            ],
            ordered=False
        )

    def test_state_access(self):
        AuthUtils.add_permission_to_user_by_name('charlink.view_state', self.user)
        corps = get_visible_corps(self.user)
        self.assertQuerysetEqual(
            corps,
            [
                self.corporation3,
            ],
            ordered=False
        )

    def test_state_and_alliance_access(self):
        AuthUtils.add_permissions_to_user_by_name(['charlink.view_state', 'charlink.view_alliance'], self.user)
        corps = get_visible_corps(self.user)
        self.assertQuerysetEqual(
            corps,
            [
                self.corporation,
                self.corporation2,
                self.corporation3,
            ],
            ordered=False
        )

    def test_no_access(self):
        corps = get_visible_corps(self.user)
        self.assertQuerysetEqual(
            corps,
            [],
            ordered=False
        )
