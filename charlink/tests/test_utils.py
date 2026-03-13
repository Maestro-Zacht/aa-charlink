from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import Group, User, Permission

from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory
from app_utils.testing import create_state

from charlink.utils import get_visible_corps, chars_annotate_linked_apps, get_user_available_apps, get_user_linked_chars, permissions_q, users_with_permission
from charlink.app_imports import import_apps
from charlink.imports.corptools import _corp_perms
from charlink.models import AppSettings


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
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


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestCharsAnnotateLinkedApps(TestCase):

    @classmethod
    def setUpTestData(cls):
        EveCharacterFactory.create_batch(10)

    def test_ok(self):
        chars = EveCharacter.objects.all()
        imported_apps = import_apps()

        res = chars_annotate_linked_apps(chars, [imported_apps['allianceauth.authentication'].imports[0]])

        self.assertEqual(len(res), 10)
        for char in res:
            self.assertTrue(hasattr(char, 'allianceauth.authentication_default'))


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestGetUserAvailableApps(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["memberaudit.basic_access"])
        cls.corptools_user_corp = UserMainFactory(permissions=_corp_perms)
        cls.corptools_user_charaudit = UserMainFactory(permissions=["corptools.view_characteraudit"])

    def test_ok(self):
        import_apps()

        res = get_user_available_apps(self.user)
        self.assertSetEqual(
            set(res.keys()),
            {'memberaudit', 'allianceauth.authentication', 'testauth.testapp'}
        )

        res2 = get_user_available_apps(self.corptools_user_corp)
        self.assertSetEqual(
            set(res2.keys()),
            {'allianceauth.authentication', 'corptools', 'testauth.testapp'}
        )

        res3 = get_user_available_apps(self.corptools_user_charaudit)
        self.assertSetEqual(
            set(res3.keys()),
            {'allianceauth.authentication', 'corptools', 'testauth.testapp'}
        )

    def test_ignore(self):
        import_apps()
        AppSettings.objects.filter(app_name__startswith='corptools').update(ignored=True)

        res = get_user_available_apps(self.corptools_user_corp)
        self.assertSetEqual(
            set(res.keys()),
            {'allianceauth.authentication', 'testauth.testapp'}
        )

        res2 = get_user_available_apps(self.corptools_user_charaudit)
        self.assertSetEqual(
            set(res2.keys()),
            {'allianceauth.authentication', 'testauth.testapp'}
        )

    def test_partial_ignore(self):
        import_apps()
        AppSettings.objects.filter(app_name='corptools_structures').update(ignored=True)

        res = get_user_available_apps(self.corptools_user_corp)
        self.assertSetEqual(
            set(res.keys()),
            {'allianceauth.authentication', 'testauth.testapp'}
        )

        res2 = get_user_available_apps(self.corptools_user_charaudit)
        self.assertSetEqual(
            set(res2.keys()),
            {'allianceauth.authentication', 'corptools', 'testauth.testapp'}
        )


@patch('charlink.app_imports._imported', False)
@patch('charlink.app_imports._duplicated_apps', set())
@patch('charlink.app_imports._supported_apps', {})
@patch('charlink.app_imports._failed_to_import', {})
@patch('charlink.app_imports._no_import', [])
class TestGetUserLinkedChars(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory()

    def test_ok(self):
        res = get_user_linked_chars(self.user)

        self.assertIn('apps', res)
        self.assertIn('characters', res)


class TestPermissionsQ(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.permission1 = AuthUtils.get_permission_by_name("corptools.view_characteraudit")
        cls.permission2 = AuthUtils.get_permission_by_name("afat.manage_afat")
        cls.group, _ = Group.objects.get_or_create(name="Test Group")
        # AuthUtils.add_permissions_to_groups([cls.permission], [cls.group])
        cls.state = AuthUtils.create_state(name="Test State", priority=75)
        # cls.state.permissions.add(cls.permission)

        cls.user_1 = AuthUtils.create_user("User1")
        cls.user_2 = AuthUtils.create_user("User2")
        cls.user_3 = User.objects.create_superuser("Superuser")

    @staticmethod
    def user_with_permission_pks(perms, require_all) -> set[int]:
        users = User.objects.filter(permissions_q(perms, require_all)).distinct()
        return set(users.values_list('pk', flat=True))

    @staticmethod
    def get_perm_str(perm: Permission) -> str:
        return f"{perm.content_type.app_label}.{perm.codename}"

    def test_str_perm(self):
        AuthUtils.add_permissions_to_user([self.permission1], self.user_1)

        result = TestPermissionsQ.user_with_permission_pks(TestPermissionsQ.get_perm_str(self.permission1), require_all=False)

        self.assertSetEqual(result, {self.user_1.pk, self.user_3.pk})

    def test_empty_perms(self):
        result = TestPermissionsQ.user_with_permission_pks([], require_all=False)
        self.assertEqual(len(result), User.objects.count())

    def test_invalid_perm_format(self):
        with self.assertRaises(ValueError):
            TestPermissionsQ.user_with_permission_pks("invalid_perm_format", require_all=False)

    def test_permission_to_user(self):
        AuthUtils.add_permissions_to_user([self.permission1], self.user_1)

        result = TestPermissionsQ.user_with_permission_pks([TestPermissionsQ.get_perm_str(self.permission1)], require_all=False)

        self.assertSetEqual(result, {self.user_1.pk, self.user_3.pk})

    def test_permission_to_group(self):
        AuthUtils.add_permissions_to_groups([self.permission1], [self.group])
        self.user_1.groups.add(self.group)
        self.assertSetEqual(
            TestPermissionsQ.user_with_permission_pks(
                [TestPermissionsQ.get_perm_str(self.permission1)],
                require_all=False
            ),
            {self.user_1.pk, self.user_3.pk}
        )

    def test_permission_to_state(self):
        self.state.permissions.add(self.permission1)
        AuthUtils.assign_state(self.user_1, self.state, disconnect_signals=True)
        self.assertSetEqual(
            TestPermissionsQ.user_with_permission_pks(
                [TestPermissionsQ.get_perm_str(self.permission1)],
                require_all=False
            ),
            {self.user_1.pk, self.user_3.pk}
        )

    def test_multiple_assignments(self):
        AuthUtils.add_permissions_to_user([self.permission1], self.user_1)

        AuthUtils.add_permissions_to_groups([self.permission1], [self.group])
        self.user_1.groups.add(self.group)

        self.state.permissions.add(self.permission1)
        AuthUtils.assign_state(self.user_1, self.state, disconnect_signals=True)

        result = TestPermissionsQ.user_with_permission_pks([TestPermissionsQ.get_perm_str(self.permission1)], require_all=False)

        self.assertSetEqual(result, {self.user_1.pk, self.user_3.pk})

    def test_require_any(self):
        AuthUtils.add_permissions_to_user([self.permission1], self.user_1)

        AuthUtils.add_permissions_to_groups([self.permission2], [self.group])
        self.user_2.groups.add(self.group)

        result = TestPermissionsQ.user_with_permission_pks(
            [TestPermissionsQ.get_perm_str(self.permission1), TestPermissionsQ.get_perm_str(self.permission2)],
            require_all=False
        )

        self.assertSetEqual(result, {self.user_1.pk, self.user_2.pk, self.user_3.pk})

    def test_require_all(self):
        AuthUtils.add_permissions_to_user([self.permission1], self.user_1)

        AuthUtils.add_permissions_to_groups([self.permission1], [self.group])
        self.user_2.groups.add(self.group)

        self.state.permissions.add(self.permission2)
        AuthUtils.assign_state(self.user_2, self.state, disconnect_signals=True)

        result = TestPermissionsQ.user_with_permission_pks(
            [TestPermissionsQ.get_perm_str(self.permission1), TestPermissionsQ.get_perm_str(self.permission2)],
            require_all=True
        )

        self.assertSetEqual(result, {self.user_2.pk, self.user_3.pk})

    @patch('charlink.utils.permissions_q')
    def test_users_with_permission_calls_permissions_q(self, mock_permissions_q):
        perms = [TestPermissionsQ.get_perm_str(self.permission1)]
        users_with_permission(perms, require_all=True)
        mock_permissions_q.assert_called_once_with(perms, True)
