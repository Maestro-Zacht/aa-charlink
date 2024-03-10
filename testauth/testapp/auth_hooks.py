from allianceauth import hooks


@hooks.register('charlink')
def register_charlink_hook():
    return 'testauth.testapp.charlink_hook'


@hooks.register('charlink')
def register_charlink_hook_invalid():
    return 'testauth.testapp.charlink_hook_invalid'


@hooks.register('charlink')
def register_charlink_hook_no_file():
    return 'testauth.testapp.charlink_hook_no_file'


@hooks.register('charlink')
def register_charlink_hook_no_app_import():
    return 'testauth.testapp.charlink_hook_no_import'
