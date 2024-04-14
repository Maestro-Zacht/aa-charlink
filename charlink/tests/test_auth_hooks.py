from django.test import TestCase
from django.urls import reverse

from app_utils.testdata_factories import UserMainFactory


class TestHooks(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.testuser = UserMainFactory()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.html_menu = f"""
            <li class="d-flex flex-wrap m-2 p-2 pt-0 pb-0 mt-0 mb-0 me-0 pe-0">
                <i class="nav-link fas fa-link fa-fw align-self-center me-3 active"></i>
                <a class="nav-link flex-fill align-self-center me-auto active" href="{reverse('charlink:index')}">
                    CharLink
                </a>
            </li>
        """
        cls.html_dashboard = (
            f'<form method="post" action="{reverse("charlink:dashboard_post")}">'
        )

    def test_menu_hook(self):
        self.client.force_login(self.testuser)

        response = self.client.get(reverse("charlink:index"))
        self.assertContains(response, self.html_menu, html=True)

    def test_dashboard_hook(self):
        self.client.force_login(self.testuser)

        response = self.client.get(reverse("authentication:dashboard"))
        self.assertContains(response, self.html_dashboard, status_code=200)
