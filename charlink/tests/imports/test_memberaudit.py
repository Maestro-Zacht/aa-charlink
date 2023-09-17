from unittest.mock import patch

from django.test import TestCase, RequestFactory

from app_utils.testdata_factories import UserMainFactory
from app_utils.testing import create_authgroup

from charlink.imports.memberaudit import add_character, is_character_added

from memberaudit.app_settings import MEMBERAUDIT_TASKS_NORMAL_PRIORITY
from memberaudit.models import ComplianceGroupDesignation


class TestAddCharacter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["memberaudit.basic_access"])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        request = self.factory.get('/charlink/login/')
        request.user = self.user
        token = self.user.token_set.first()

        add_character(request, token)

        mock_update_character.assert_called_once()
        self.assertTrue(is_character_added(self.character))

    @patch('memberaudit.tasks.update_compliance_groups_for_user.apply_async')
    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok_compliance(self, mock_update_character, mock_update_compliance):
        mock_update_character.return_value = None
        mock_update_compliance.return_value = None

        request = self.factory.get('/charlink/login/')
        request.user = self.user
        token = self.user.token_set.first()

        group = create_authgroup()
        ComplianceGroupDesignation.objects.create(group=group)

        add_character(request, token)

        mock_update_character.assert_called_once()
        mock_update_compliance.assert_called_once_with(
            args=[self.user.pk],
            priority=MEMBERAUDIT_TASKS_NORMAL_PRIORITY
        )
        self.assertTrue(is_character_added(self.character))


class TestIsCharacterAdded(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=["memberaudit.basic_access"])
        cls.character = cls.user.profile.main_character
        cls.factory = RequestFactory()

    @patch('memberaudit.tasks.update_character.apply_async')
    def test_ok(self, mock_update_character):
        mock_update_character.return_value = None

        self.assertFalse(is_character_added(self.character))
        add_character(self.factory.get('/charlink/login/'), self.user.token_set.first())
        self.assertTrue(is_character_added(self.character))
