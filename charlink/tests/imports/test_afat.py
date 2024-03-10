from django.test import TestCase

from charlink.app_imports import import_apps

from app_utils.testdata_factories import UserMainFactory, EveCharacterFactory
from app_utils.testing import add_character_to_user


_scopes_readfleet = ["esi-fleets.read_fleet.v1"]
_scopes_clickfleet = ["esi-location.read_location.v1", "esi-location.read_ship_type.v1", "esi-location.read_online.v1"]


class TestAddCharacter(TestCase):

    def test_ok(self):
        app_import = import_apps()['afat']

        self.assertIsNone(app_import.get('readfleet').add_character(None))
        self.assertIsNone(app_import.get('clickfat').add_character(None))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()
        cls.main_character = cls.user.profile.main_character

        cls.char_readfleet = EveCharacterFactory()
        add_character_to_user(cls.user, cls.char_readfleet, scopes=_scopes_readfleet)
        cls.char_clickfat = EveCharacterFactory()
        add_character_to_user(cls.user, cls.char_clickfat, scopes=_scopes_clickfleet)

    def test_ok(self):
        app_import = import_apps()['afat']

        self.assertFalse(app_import.get('readfleet').is_character_added(self.main_character))
        self.assertTrue(app_import.get('readfleet').is_character_added(self.char_readfleet))
        self.assertFalse(app_import.get('readfleet').is_character_added(self.char_clickfat))

        self.assertFalse(app_import.get('clickfat').is_character_added(self.main_character))
        self.assertFalse(app_import.get('clickfat').is_character_added(self.char_readfleet))
        self.assertTrue(app_import.get('clickfat').is_character_added(self.char_clickfat))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.manage_user = UserMainFactory(permissions=['afat.manage_afat'])
        cls.add_fatlink_user = UserMainFactory(permissions=['afat.add_fatlink'])
        cls.both_user = UserMainFactory(permissions=['afat.manage_afat', 'afat.add_fatlink'])
        cls.basic_access_user = UserMainFactory(permissions=['afat.basic_access'])
        cls.no_perm_user = UserMainFactory()

    def test_ok(self):
        app_import = import_apps()['afat']

        self.assertTrue(app_import.get('readfleet').check_permissions(self.manage_user))
        self.assertTrue(app_import.get('readfleet').check_permissions(self.add_fatlink_user))
        self.assertTrue(app_import.get('readfleet').check_permissions(self.both_user))
        self.assertFalse(app_import.get('readfleet').check_permissions(self.no_perm_user))

        self.assertFalse(app_import.get('clickfat').check_permissions(self.no_perm_user))
        self.assertTrue(app_import.get('clickfat').check_permissions(self.basic_access_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.manage_user = UserMainFactory(permissions=['afat.manage_afat'])
        cls.add_fatlink_user = UserMainFactory(permissions=['afat.add_fatlink'])
        cls.both_user = UserMainFactory(permissions=['afat.manage_afat', 'afat.add_fatlink'])
        cls.basic_access_user = UserMainFactory(permissions=['afat.basic_access'])
        cls.no_perm_user = UserMainFactory()

    def test_ok(self):
        app_import = import_apps()['afat']

        users_readfleet = app_import.get('readfleet').get_users_with_perms()
        self.assertQuerysetEqual(
            users_readfleet,
            [
                self.manage_user.pk,
                self.add_fatlink_user.pk,
                self.both_user.pk
            ],
            ordered=False,
            transform=lambda x: x.pk
        )

        users_clickfat = app_import.get('clickfat').get_users_with_perms()
        self.assertQuerysetEqual(
            users_clickfat,
            [
                self.basic_access_user.pk
            ],
            transform=lambda x: x.pk
        )
