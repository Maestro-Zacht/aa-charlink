from unittest.mock import patch

from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import create_authgroup

from charlink.imports.memberaudit import _add_character, _is_character_added
from charlink.app_imports import import_apps

from memberaudit.app_settings import MEMBERAUDIT_TASKS_NORMAL_PRIORITY
from memberaudit.models import ComplianceGroupDesignation


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["memberaudit.basic_access"])
        cls.character = cls.user.profile.main_character

    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        token = self.user.token_set.first()

        _add_character(token)

        mock_update_character.assert_called_once()
        self.assertTrue(_is_character_added(self.character))

    @patch('memberaudit.tasks.update_compliance_groups_for_user.apply_async')
    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok_compliance(self, mock_update_character, mock_update_compliance):
        mock_update_character.return_value = None
        mock_update_compliance.return_value = None

        token = self.user.token_set.first()

        group = create_authgroup()
        ComplianceGroupDesignation.objects.create(group=group)

        _add_character(token)

        mock_update_character.assert_called_once()
        mock_update_compliance.assert_called_once_with(
            args=[self.user.pk],
            priority=MEMBERAUDIT_TASKS_NORMAL_PRIORITY
        )
        self.assertTrue(_is_character_added(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["memberaudit.basic_access"])
        cls.character = cls.user.profile.main_character

    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        self.assertFalse(_is_character_added(self.character))
        _add_character(self.user.token_set.first())
        self.assertTrue(_is_character_added(self.character))


class TestCheckPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["memberaudit.basic_access"])

    def test_ok(self):
        login_import = import_apps()['memberaudit'].get('default')

        self.assertTrue(login_import.check_permissions(self.perm_user))
        self.assertFalse(login_import.check_permissions(self.no_perm_user))


class TestGetUsersWithPerms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.no_perm_user = UserMainFactory()
        cls.perm_user = UserMainFactory(permissions=["memberaudit.basic_access"])

    def test_ok(self):
        login_import = import_apps()['memberaudit'].get('default')

        users = login_import.get_users_with_perms()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.perm_user)
