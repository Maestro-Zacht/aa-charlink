from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from django import template

register = template.Library()


@register.filter
def get_corp_members(corp: EveCorporationInfo):
    return EveCharacter.objects.filter(
        corporation_id=corp.corporation_id
    ).select_related("character_ownership__user__profile__main_character")


@register.filter
def get_char_attr(character_obj, attr: str):
    if isinstance(character_obj, str):
        try:
            character_obj = int(character_obj)
        except ValueError:
            return ""

    if isinstance(character_obj, EveCharacter):
        return getattr(character_obj, attr, "")
    if isinstance(character_obj, int):
        try:
            return getattr(EveCharacter.objects.get(pk=character_obj), attr, "")
        except EveCharacter.DoesNotExist:
            return ""
    return ""
