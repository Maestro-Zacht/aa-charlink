from unittest.mock import patch, Mock

from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages, DEFAULT_LEVELS

from app_utils.testdata_factories import UserMainFactory, EveCorporationInfoFactory, EveCharacterFactory

from charlink.views import get_navbar_elements
from charlink.imports.memberaudit import scopes as memberaudit_scopes, permissions as memberaudit_permissions
from charlink.imports.miningtaxes import scopes as miningtaxes_scopes
from charlink.imports.moonmining import scopes as moonmining_scopes, permissions as moonmining_permissions


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


class TestIndex(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(permissions=[
            'corputils.add_corpstats',
            'memberaudit.basic_access',
            'miningtaxes.basic_access',
            'moonmining.add_refinery_owner',
            'moonmining.basic_access',
            'corpstats.add_corpstat',
        ])

        cls.form_data = {
            'allianceauth.corputils': ['on'],
            'memberaudit': ['on'],
            'miningtaxes': ['on'],
            'moonmining': ['on'],
            'corpstats': ['on'],
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
        self.assertIn('apps', session['charlink'])
        self.assertIn('add_character', session['charlink']['apps'])
        self.assertIn('allianceauth.corputils', session['charlink']['apps'])
        self.assertIn('memberaudit', session['charlink']['apps'])
        self.assertIn('miningtaxes', session['charlink']['apps'])
        self.assertIn('moonmining', session['charlink']['apps'])
        self.assertIn('corpstats', session['charlink']['apps'])
        self.assertEqual(len(session['charlink']['apps']), 6)

    # form always valid
    # def test_post_wrong_data(self):
    #     self.client.force_login(self.user)

    #     res = self.client.post(reverse('charlink:index'), {'add_character:': '5'})

    #     self.assertEqual(res.status_code, 200)
    #     self.assertIn('form', res.context)
    #     self.assertIn('characters_added', res.context)


class TestLoginView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserMainFactory(
            permissions=[
                'memberaudit.basic_access',
                'miningtaxes.basic_access',
            ],
            main_character__scopes=list(set(memberaudit_scopes + miningtaxes_scopes))
        )
        cls.token = cls.user.token_set.first()

    @patch('charlink.views.import_apps')
    @patch('charlink.decorators.token_required')
    def test_ok(self, mock_token_required, mock_import_apps):
        session = self.client.session
        session['charlink'] = {
            'scopes': list(set(memberaudit_scopes + miningtaxes_scopes)),
            'apps': ['memberaudit', 'miningtaxes', 'add_character'],
        }
        session.save()

        def fake_decorator(f):
            def fake_wrapper(request, *args, **kwargs):
                return f(request, self.token, *args, **kwargs)
            return fake_wrapper

        mock_token_required.return_value = fake_decorator

        mock_import_apps.return_value = {
            'memberaudit': {
                'field_label': 'Member Audit',
                'add_character': lambda request, token: None,
                'permissions': ['memberaudit.basic_access'],
                'scopes': memberaudit_scopes,
            },
            'miningtaxes': {
                'field_label': 'Mining Taxes',
                'add_character': Mock(side_effect=Exception('test')),
                'permissions': ['miningtaxes.basic_access'],
                'scopes': miningtaxes_scopes,
            },
            'add_character': {
                'field_label': 'Add Character',
                'add_character': lambda request, token: None,
                'permissions': [],
                'scopes': [],
            },
        }

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
        cls.user = UserMainFactory(permissions=[
            'charlink.view_corp',
            *memberaudit_permissions,
            *moonmining_permissions,
        ])
        char2, char3 = EveCharacterFactory.create_batch(
            2,
            corporation=cls.user.profile.main_character.corporation
        )
        cls.user2 = UserMainFactory(
            permissions=memberaudit_permissions + moonmining_permissions,
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
        self.assertIn('characters', res.context)
        self.assertEqual(len(res.context['characters']), 2)
        self.assertIn('app', res.context)
        self.assertIn('app_data', res.context)

    def test_app_empty_perms(self):
        self.client.force_login(self.user)

        res = self.client.get(reverse('charlink:audit_app', args=['corptools']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('characters', res.context)
        self.assertEqual(len(res.context['characters']), 3)
        self.assertIn('app', res.context)
        self.assertIn('app_data', res.context)

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
            permissions=moonmining_permissions,
            main_character__character=extra_char
        )

        res = self.client.get(reverse('charlink:audit_app', args=['moonmining']))

        self.assertEqual(res.status_code, 200)
        self.assertIn('characters', res.context)
        self.assertEqual(len(res.context['characters']), 3)
        self.assertIn('app', res.context)
        self.assertIn('app_data', res.context)
