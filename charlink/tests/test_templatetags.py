from app_utils.testdata_factories import EveCharacterFactory, UserMainFactory
from django.template import Context, Template
from django.test import TestCase


class TestGetCorpMembersFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.testuser = UserMainFactory()
        cls.testcorp = cls.testuser.profile.main_character.corporation

        cls.corpmates = [
            *EveCharacterFactory.create_batch(5, corporation=cls.testcorp),
            cls.testuser.profile.main_character,
        ]

        cls.template = Template(
            "{% load charlinkutils %}{% for char in corp|get_corp_members %}{{ char.character_name }},{% endfor %}"
        )

    def test_success(self):
        context = Context({"corp": self.testcorp})

        res = self.template.render(context)

        for char in self.corpmates:
            self.assertIn(char.character_name, res)


class TestGetCharAttrFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.testuser = UserMainFactory()
        cls.testcharacter = cls.testuser.profile.main_character

        cls.template = Template(
            '{% load charlinkutils %}{{ char|get_char_attr:"character_name" }}'
        )

        cls.missing_attr_template = Template(
            '{% load charlinkutils %}{{ char|get_char_attr:"does_not_exist" }}'
        )

    def test_character_success(self):
        context = Context({"char": self.testcharacter})

        res = self.template.render(context)

        self.assertEqual(res, self.testcharacter.character_name)

    def test_int_success(self):
        context = Context({"char": self.testcharacter.pk})

        res = self.template.render(context)

        self.assertEqual(res, self.testcharacter.character_name)

    def test_int_fail(self):
        context = Context({"char": self.testcharacter.pk + 10})

        res = self.template.render(context)

        self.assertEqual(res, "")

    def test_str_fail(self):
        context = Context({"char": "notanumber"})

        res = self.template.render(context)

        self.assertEqual(res, "")

    def test_str_success(self):
        context = Context({"char": str(self.testcharacter.pk)})

        res = self.template.render(context)

        self.assertEqual(res, self.testcharacter.character_name)

    def test_param_not_valid(self):
        context = Context({"char": []})

        res = self.template.render(context)

        self.assertEqual(res, "")

    def test_character_missing_attr(self):
        context = Context({"char": self.testcharacter})

        res = self.missing_attr_template.render(context)

        self.assertEqual(res, "")

    def test_int_missing_attr(self):
        context = Context({"char": self.testcharacter.pk})

        res = self.missing_attr_template.render(context)

        self.assertEqual(res, "")
