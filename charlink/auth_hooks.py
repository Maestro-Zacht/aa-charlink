from allianceauth import hooks
from allianceauth.services.hooks import UrlHook, MenuItemHook

from . import urls
from .views import dashboard_login
from .models import ComplianceFilter


class CharlinkMenuItemHook(MenuItemHook):
    def __init__(self):
        super().__init__("CharLink", "fas fa-link", "charlink:index", navactive=['charlink:'])


class LoginDashboardHook(hooks.DashboardItemHook):
    def __init__(self):
        super().__init__(
            dashboard_login,
            6
        )


@hooks.register('menu_item_hook')
def register_menu():
    return CharlinkMenuItemHook()


@hooks.register('url_hook')
def register_urls():
    return UrlHook(urls, 'charlink', 'charlink/')


@hooks.register('dashboard_hook')
def register_login_hook():
    return LoginDashboardHook()


@hooks.register('secure_group_filters')
def securegroups_filters():
    return [ComplianceFilter]
