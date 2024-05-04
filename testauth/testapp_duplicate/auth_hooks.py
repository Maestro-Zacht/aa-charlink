from allianceauth import hooks


@hooks.register('charlink')
def register_charlink_hook():
    return 'testauth.testapp_duplicate.charlink_hook_duplicate_1'


@hooks.register('charlink')
def register_charlink_hook():
    return 'testauth.testapp_duplicate.charlink_hook_duplicate_2'
