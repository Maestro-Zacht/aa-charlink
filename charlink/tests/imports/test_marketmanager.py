from django.test import TestCase
from marketmanager.views import CHARACTER_SCOPES, CORPORATION_SCOPES

from charlink.app_imports import import_apps
from charlink.tests.factories import (
    add_character_to_user,
    create_eve_character,
    create_user_main,
)


class TestIsCharacterAdded(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user_main()
        cls.main_character = cls.user.profile.main_character

        cls.login_char = create_eve_character()
        add_character_to_user(cls.user, cls.login_char, scopes=CHARACTER_SCOPES)
        cls.login_corp = create_eve_character()
        add_character_to_user(cls.user, cls.login_corp, scopes=CORPORATION_SCOPES)

    def test_ok_character_login(self):
        app_import = import_apps()["marketmanager"]

        self.assertFalse(
            app_import.get("character").is_character_added(self.main_character)
        )
        self.assertTrue(app_import.get("character").is_character_added(self.login_char))
        self.assertFalse(
            app_import.get("character").is_character_added(self.login_corp)
        )

    def test_ok_corporation_login(self):
        app_import = import_apps()["marketmanager"]

        self.assertFalse(
            app_import.get("corporation").is_character_added(self.main_character)
        )
        self.assertFalse(
            app_import.get("corporation").is_character_added(self.login_char)
        )
        self.assertTrue(
            app_import.get("corporation").is_character_added(self.login_corp)
        )


class TestAddCharacter(TestCase):
    def test_ok(self):
        app_import = import_apps()["marketmanager"]

        self.assertIsNone(app_import.get("character").add_character(None, None))
        self.assertIsNone(app_import.get("corporation").add_character(None, None))


class TestCheckPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.basic_market_browser_user = create_user_main(
            permissions=["marketmanager.basic_market_browser"]
        )
        cls.no_perm_user = create_user_main()

    def test_ok(self):
        app_import = import_apps()["marketmanager"]

        self.assertTrue(
            app_import.get("character").check_permissions(
                self.basic_market_browser_user
            )
        )
        self.assertTrue(
            app_import.get("corporation").check_permissions(
                self.basic_market_browser_user
            )
        )
        self.assertFalse(
            app_import.get("character").check_permissions(self.no_perm_user)
        )
        self.assertFalse(
            app_import.get("corporation").check_permissions(self.no_perm_user)
        )


class TestGetUsersWithPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.basic_market_browser_user = create_user_main(
            permissions=["marketmanager.basic_market_browser"]
        )
        cls.no_perm_user = create_user_main()

    def test_ok(self):
        app_import = import_apps()["marketmanager"]

        self.assertQuerySetEqual(
            app_import.get("character").get_users_with_perms(),
            [self.basic_market_browser_user.pk],
            ordered=False,
            transform=lambda x: x.pk,
        )
        self.assertQuerySetEqual(
            app_import.get("corporation").get_users_with_perms(),
            [self.basic_market_browser_user.pk],
            ordered=False,
            transform=lambda x: x.pk,
        )
