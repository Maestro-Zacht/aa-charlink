from unittest.mock import patch, Mock

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages, DEFAULT_LEVELS
from django.db.models import OuterRef, Exists

from allianceauth.authentication.models import CharacterOwnership

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory

from charlink.views import get_navbar_elements, dashboard_login
from charlink.imports.memberaudit import app_import as memberaudit_import
from charlink.imports.miningtaxes import app_import as miningtaxes_import
from charlink.imports.corptools import _corp_perms
from charlink.app_imports.utils import AppImport, LoginImport


class TestGetNavbarElements(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.permuser = UserMainFactory(permissions=['charlink.view_corp'])
        cls.nopermuser = UserMainFactory()

    def test_with_perm(self):
        res = get_navbar_elements(self.permuser)

        self.assertIn('available', res)
        self.assertTrue(res['is_auditor'])

        self.assertIn('available', res)
        self.assertGreater(len(res['available']), 0)

        self.assertIn('available_apps', res)
        self.assertGreater(len(res['available_apps']), 0)

    def test_without_perm(self):
        res = get_navbar_elements(self.nopermuser)

        self.assertIn('available', res)
        self.assertFalse(res['is_auditor'])

        self.assertIn('available', res)
        self.assertEqual(len(res['available']), 0)

        self.assertIn('available_apps', res)
        self.assertEqual(len(res['available_apps']), 0)


class TestDashboardLogin(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                'memberaudit.basic_access',
                'miningtaxes.basic_access',
            ]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        request_factory = RequestFactory()
        cls.request = request_factory.get('/fake')
        cls.request.user = cls.user

        cls.form_contents = [
            '''<div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="charlink-allianceauth.authentication_default" class="form-check-input" disabled id="id_charlink-allianceauth.authentication_default" checked>
                    <label class="form-check-label" for="id_charlink-allianceauth.authentication_default">Add Character (default)</label>
                </div>
            </div>''',
            '''<div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="charlink-memberaudit_default" class="form-check-input" id="id_charlink-memberaudit_default" checked>
                    <label class="form-check-label" for="id_charlink-memberaudit_default">Member Audit</label>
                </div>
            </div>''',
            '''<div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="charlink-miningtaxes_default" class="form-check-input" id="id_charlink-miningtaxes_default" checked>
                    <label class="form-check-label" for="id_charlink-miningtaxes_default">Mining Taxes</label>
                </div>
            </div>''',
            '''<div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="charlink-testauth.testapp_default" class="form-check-input" id="id_charlink-testauth.testapp_default" checked>
                    <label class="form-check-label" for="id_charlink-testauth.testapp_default">TestApp</label>
                </div>
            </div>''',
            '''<div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" name="charlink-testauth.testapp_import2" class="form-check-input" id="id_charlink-testauth.testapp_import2" checked>
                    <label class="form-check-label" for="id_charlink-testauth.testapp_import2">TestApp2</label>
                </div>
            </div>''',
        ]

    def test_ok(self):
        res = dashboard_login(self.request)
        self.assertInHTML('<h4 class="card-title mb-3">CharLink</h4>', res)
        for content in self.form_contents:
            self.assertInHTML(content, res)


class TestDashboardPost(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                'corputils.add_corpstats',
                'memberaudit.basic_access',
                'miningtaxes.basic_access',
                'moonmining.add_refinery_owner',
                'moonmining.basic_access',
                'corpstats.add_corpstat',
            ]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form_data = {
            'charlink-allianceauth.corputils_default': ['on'],
            'charlink-miningtaxes_default': ['on'],
            'charlink-moonmining_default': ['on'],
            'charlink-corpstats_default': ['on'],
        }

    def test_post_ok(self):
        self.client.force_login(self.user)

        res = self.client.post(reverse('charlink:dashboard_post'), self.form_data)

        self.assertRedirects(
            res,
            reverse('charlink:login'),
            fetch_redirect_response=False
        )

        session = self.client.session

        self.assertIn('charlink', session)
        self.assertIn('scopes', session['charlink'])
        self.assertIn('imports', session['charlink'])

        converted_imports = [list(x) for x in session['charlink']['imports']]

        self.assertIn(['allianceauth.authentication', 'default'], converted_imports)
        self.assertIn(['allianceauth.corputils', 'default'], converted_imports)
        self.assertNotIn(['memberaudit', 'default'], converted_imports)
        self.assertIn(['miningtaxes', 'default'], converted_imports)
        self.assertIn(['moonmining', 'default'], converted_imports)
        self.assertIn(['corpstats', 'default'], converted_imports)
        self.assertEqual(len(session['charlink']['imports']), 5)

    def test_get(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:dashboard_post'))

        self.assertRedirects(res, reverse('charlink:index'))

        messages = list(get_messages(res.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, DEFAULT_LEVELS['ERROR'])
        self.assertEqual(messages[0].message, 'Invalid request')

    # force form invalid
    @patch('charlink.forms.LinkForm.is_valid')
    def test_form_invalid(self, mock_is_valid):
        mock_is_valid.return_value = False

        self.client.force_login(self.user)
        res = self.client.post(reverse('charlink:dashboard_post'), self.form_data)

        self.assertRedirects(res, reverse('authentication:dashboard'))

        messages = list(get_messages(res.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, DEFAULT_LEVELS['ERROR'])
        self.assertEqual(messages[0].message, 'Invalid form data')


class TestIndex(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                'corputils.add_corpstats',
                'memberaudit.basic_access',
                'miningtaxes.basic_access',
                'moonmining.add_refinery_owner',
                'moonmining.basic_access',
                'corpstats.add_corpstat',
            ]
        )

        cls.form_data = {
            'allianceauth.corputils_default': ['on'],
            'miningtaxes_default': ['on'],
            'moonmining_default': ['on'],
            'corpstats_default': ['on'],
        }

    def test_get(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:index'))

        self.assertEqual(res.status_code, 200)
        self.assertIn('form', res.context)
        self.assertIn('characters_added', res.context)

    def test_post_ok(self):
        self.client.force_login(self.user)

        res = self.client.post(reverse('charlink:index'), self.form_data)

        self.assertRedirects(
            res,
            reverse('charlink:login'),
            fetch_redirect_response=False
        )

        session = self.client.session

        self.assertIn('charlink', session)
        self.assertIn('scopes', session['charlink'])
        self.assertIn('imports', session['charlink'])

        converted_imports = [list(x) for x in session['charlink']['imports']]

        self.assertIn(['allianceauth.authentication', 'default'], converted_imports)
        self.assertIn(['allianceauth.corputils', 'default'], converted_imports)
        self.assertNotIn(['memberaudit', 'default'], converted_imports)
        self.assertIn(['miningtaxes', 'default'], converted_imports)
        self.assertIn(['moonmining', 'default'], converted_imports)
        self.assertIn(['corpstats', 'default'], converted_imports)
        self.assertEqual(len(session['charlink']['imports']), 5)

    # form always valid
    # def test_post_wrong_data(self):
    #     self.client.force_login(self.user)

    #     res = self.client.post(reverse('charlink:index'), {'allianceauth.authentication:': '5'})

    #     self.assertEqual(res.status_code, 200)
    #     self.assertIn('form', res.context)
    #     self.assertIn('characters_added', res.context)

    # force form invalid
    @patch('charlink.forms.LinkForm.is_valid')
    def test_form_invalid(self, mock_is_valid):
        mock_is_valid.return_value = False

        self.client.force_login(self.user)
        res = self.client.post(reverse('charlink:index'), self.form_data)

        self.assertEqual(res.status_code, 200)
        self.assertIn('form', res.context)
        self.assertIn('characters_added', res.context)


class TestLoginView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.scopes = list(set(memberaudit_import.imports[0].scopes + miningtaxes_import.imports[0].scopes))
        cls.user = UserMainFactory(
            permissions=[
                'memberaudit.basic_access',
                'miningtaxes.basic_access',
            ],
            main_character__scopes=cls.scopes
        )
        cls.token = cls.user.token_set.first()

    @patch('charlink.imports.miningtaxes._add_character')
    @patch('charlink.imports.memberaudit._add_character')
    @patch('charlink.views.import_apps')
    @patch('charlink.decorators.token_required')
    def test_ok(self, mock_token_required, mock_import_apps, mock_memberaudit_add_character, mock_miningtaxes_add_character):
        session = self.client.session
        session['charlink'] = {
            'scopes': self.scopes,
            'imports': [
                ('memberaudit', 'default'),
                ('miningtaxes', 'default'),
                ('allianceauth.authentication', 'default'),
            ],
        }
        session.save()

        def fake_decorator(f):
            def fake_wrapper(request, *args, **kwargs):
                return f(request, self.token, *args, **kwargs)
            return fake_wrapper

        mock_token_required.return_value = fake_decorator

        mock_import_apps.return_value = {
            'memberaudit': AppImport('memberaudit', [
                LoginImport(
                    app_label='memberaudit',
                    unique_id='default',
                    field_label='Member Audit',
                    add_character=lambda token: None,
                    scopes=memberaudit_import.imports[0].scopes,
                    check_permissions=memberaudit_import.imports[0].check_permissions,
                    is_character_added=memberaudit_import.imports[0].is_character_added,
                    is_character_added_annotation=memberaudit_import.imports[0].is_character_added_annotation,
                    get_users_with_perms=memberaudit_import.imports[0].get_users_with_perms,
                )
            ]),
            'miningtaxes': AppImport('miningtaxes', [
                LoginImport(
                    app_label='miningtaxes',
                    unique_id='default',
                    field_label='Mining Taxes',
                    add_character=Mock(side_effect=Exception('test')),
                    scopes=miningtaxes_import.imports[0].scopes,
                    check_permissions=miningtaxes_import.imports[0].check_permissions,
                    is_character_added=miningtaxes_import.imports[0].is_character_added,
                    is_character_added_annotation=miningtaxes_import.imports[0].is_character_added_annotation,
                    get_users_with_perms=miningtaxes_import.imports[0].get_users_with_perms,
                )
            ]),
            'allianceauth.authentication': AppImport('allianceauth.authentication', [
                LoginImport(
                    app_label='allianceauth.authentication',
                    unique_id='default',
                    field_label='Add Character (default)',
                    add_character=lambda token: None,
                    scopes=['publicData'],
                    check_permissions=lambda user: True,
                    is_character_added=lambda character: CharacterOwnership.objects.filter(character=character).exists(),
                    is_character_added_annotation=Exists(CharacterOwnership.objects.filter(character_id=OuterRef('pk'))),
                    get_users_with_perms=lambda: None,
                )
            ]),
        }

        mock_memberaudit_add_character.return_value = None
        mock_miningtaxes_add_character.side_effect = Exception('test')

        self.client.force_login(self.user)
        res = self.client.get(reverse('charlink:login'))

        messages = list(get_messages(res.wsgi_request))

        self.assertEqual(len(messages), 2)

        sorted_messages = sorted(messages, key=lambda x: x.level)
        self.assertEqual(sorted_messages[0].level, DEFAULT_LEVELS['SUCCESS'])
        self.assertEqual(sorted_messages[1].level, DEFAULT_LEVELS['ERROR'])


class TestAudit(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['charlink.view_corp'])
        cls.corp = cls.user.profile.main_character.corporation
        cls.corp2 = EveCorporationInfoFactory()
        cls.char2 = EveCharacterFactory(corporation=cls.corp2)
        cls.user2 = UserMainFactory(main_character__character=cls.char2)

    def test_ok(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_corp', args=[self.corp.corporation_id]))

        self.assertEqual(res.status_code, 200)
        self.assertIn('selected', res.context)

    def test_no_perm(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_corp', args=[self.corp2.corporation_id]))

        self.assertNotEqual(res.status_code, 200)


class TestSearch(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['charlink.view_corp'])
        cls.main_char = cls.user.profile.main_character

        cls.user2 = UserMainFactory()
        cls.main_char2 = cls.user2.profile.main_character

    def test_ok(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:search'), {'search_string': self.main_char.character_name})

        self.assertEqual(res.status_code, 200)
        self.assertIn('search_string', res.context)
        self.assertIn('characters', res.context)
        self.assertEqual(len(res.context['characters']), 1)

    def test_not_found(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:search'), {'search_string': self.main_char2.character_name})

        self.assertEqual(res.status_code, 200)
        self.assertIn('search_string', res.context)
        self.assertIn('characters', res.context)
        self.assertEqual(len(res.context['characters']), 0)

    def test_missing_string(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:search'))

        self.assertRedirects(res, reverse('charlink:index'))


class TestAuditUser(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=['charlink.view_corp'])

        char2 = EveCharacterFactory(corporation=cls.user.profile.main_character.corporation)
        cls.user2 = UserMainFactory(main_character__character=char2)

        cls.user_ext = UserMainFactory()

    def test_ok(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_user', args=[self.user2.pk]))

        self.assertEqual(res.status_code, 200)
        self.assertIn('characters_added', res.context)

    def test_no_perm(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_user', args=[self.user_ext.pk]))

        self.assertNotEqual(res.status_code, 200)


class TestAuditApp(TestCase):

    @classmethod
    def setUpTestData(cls):
        permissions = ["memberaudit.basic_access", "moonmining.add_refinery_owner", "moonmining.basic_access"]
        cls.user = UserMainFactory(
            permissions=[
                'charlink.view_corp',
                'corptools.view_characteraudit',
                *permissions,
                *_corp_perms,
            ]
        )
        char2, char3 = EveCharacterFactory.create_batch(
            2,
            corporation=cls.user.profile.main_character.corporation
        )
        cls.user2 = UserMainFactory(
            permissions=permissions,
            main_character__character=char2
        )
        cls.random_char = EveCharacterFactory(corporation=cls.user.profile.main_character.corporation)
        cls.no_perm_user = UserMainFactory(
            permissions=['charlink.view_corp'],
            main_character__character=char3
        )

    def test_ok(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_app', args=['memberaudit']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('app', res.context)
        self.assertIn('logins', res.context)
        self.assertEqual(len(res.context['logins']), 1)
        self.assertEqual(len(list(res.context['logins'].values())[0]), 2)

    def test_app_empty_perms(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_app', args=['allianceauth.authentication']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('logins', res.context)
        self.assertEqual(len(res.context['logins']), 1)
        self.assertEqual(len(list(res.context['logins'].values())[0]), 3)
        self.assertIn('app', res.context)

    def test_missing_app(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_app', args=['invalid_app']))

        self.assertEqual(res.status_code, 404)

    def test_no_app_perm(self):
        self.client.force_login(self.no_perm_user)

        res = self.client.get(reverse('charlink:audit_app', args=['memberaudit']))

        self.assertNotEqual(res.status_code, 200)

    def test_multiple_app_perms(self):
        self.client.force_login(self.user)

        extra_char = EveCharacterFactory(corporation=self.user.profile.main_character.corporation)
        UserMainFactory(
            permissions=["moonmining.add_refinery_owner", "moonmining.basic_access"],
            main_character__character=extra_char
        )

        res = self.client.get(reverse('charlink:audit_app', args=['moonmining']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('logins', res.context)
        self.assertEqual(len(res.context['logins']), 1)
        self.assertEqual(len(list(res.context['logins'].values())[0]), 3)
        self.assertIn('app', res.context)

    def test_app_with_multiple_logins(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_app', args=['corptools']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('logins', res.context)
        self.assertEqual(len(res.context['logins']), 2)
