from allianceauth import hooks


@hooks.register('charlink')
def register_charlink_hook():
    return 'testauth.testapp.charlink_hook'
