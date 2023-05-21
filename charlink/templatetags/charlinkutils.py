from django import template

from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter

register = template.Library()


@register.filter
def get_corp_members(corp: EveCorporationInfo):
    return EveCharacter.objects.filter(corporation_id=corp.corporation_id).select_related("character_ownership__user__profile__main_character")
