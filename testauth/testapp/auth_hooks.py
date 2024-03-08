from allianceauth import hooks


@hooks.register('charlink')
def register_charlink_hook():
    return 'testapp.charlink_hook'
