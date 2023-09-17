from django.test import TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory


class TestHooks(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.testuser = UserMainFactory()
        cls.html_menu = f"""
            <li>
                <a class="active" href="{reverse('charlink:index')}">
                    <i class="fas fa-link"></i> CharLink
                </a>
            </li>
        """

    def test_render_hook(self):
        self.client.force_login(self.testuser)

        response = self.client.get(reverse('charlink:index'))
        self.assertContains(response, self.html_menu, html=True)
