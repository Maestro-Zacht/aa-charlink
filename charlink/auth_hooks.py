from allianceauth import hooks
from allianceauth.services.hooks import UrlHook, MenuItemHook

from . import urls


class CharlinkMenuItemHook(MenuItemHook):
    def __init__(self):
        super().__init__("Charlink", "fas fa-link", "charlink:index", navactive=['charlink:'])


@hooks.register('menu_item_hook')
def register_menu():
    return CharlinkMenuItemHook()


@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'charlink', 'charlink/')
