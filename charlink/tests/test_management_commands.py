from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase

from charlink.app_imports.utils import AppImport, LoginImport
from charlink.models import AppSettings


class CharlinkResetSelectionsCommandTest(TestCase):

    @patch('charlink.management.commands.charlink_reset_selections.import_apps')
    def test_handle_resets_default_selections(self, mock_import_apps):
        mock_import_apps.return_value = {
            'testapp': AppImport('testapp', [
                LoginImport(
                    app_label='testapp',
                    unique_id='default',
                    field_label='TestApp',
                    add_character=lambda request, token: None,
                    scopes=['scope1'],
                    check_permissions=lambda user: True,
                    is_character_added=lambda character: False,
                    is_character_added_annotation=Mock(),
                    get_users_with_perms=lambda: None,
                    default_initial_selection=False,
                ),
                LoginImport(
                    app_label='testapp',
                    unique_id='option2',
                    field_label='TestApp 2',
                    add_character=lambda request, token: None,
                    scopes=['scope1'],
                    check_permissions=lambda user: True,
                    is_character_added=lambda character: False,
                    is_character_added_annotation=Mock(),
                    get_users_with_perms=lambda: None,
                    default_initial_selection=True,
                ),
            ])
        }

        as1 = AppSettings.objects.create(
            app_name='testapp_default',
            default_selection=True
        )
        as2 = AppSettings.objects.create(
            app_name='testapp_option2',
            default_selection=False
        )

        out = StringIO()
        call_command('charlink_reset_selections', stdout=out)

        as1.refresh_from_db()
        as2.refresh_from_db()

        self.assertFalse(as1.default_selection)
        self.assertTrue(as2.default_selection)

        self.assertIn('Resetting login options default selections...', out.getvalue())
        self.assertIn('Reset done!', out.getvalue())
