from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse

from charlink.decorators import charlink


class TestCharlink(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()

    @patch('charlink.decorators.token_required')
    def test_ok(self, mock_token_required):
        scopes = ['esi-skills.read_skills.v1']
        session = {'charlink': {'scopes': scopes}}

        mock_token_required.return_value = lambda x: x

        @charlink
        def test_view(request):
            return 'ok'

        request = self.factory.get('/charlink/login/')
        request.session = session

        self.assertEqual(test_view(request), 'ok')
        mock_token_required.assert_called_with(scopes=scopes)

    @patch('charlink.decorators.messages.error')
    def test_missing_session(self, mock_messages_error):
        @charlink
        def test_view(request):
            return 'ok'

        request = self.factory.get('/charlink/login/')
        request.session = {}

        mock_messages_error.return_value = None

        self.assertRedirects(
            test_view(request),
            reverse('charlink:index'),
            fetch_redirect_response=False,
        )

        self.assertTrue(mock_messages_error.called)
