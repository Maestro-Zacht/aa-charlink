from allianceauth import hooks


@hooks.register('charlink')
def register_charlink_hook():
    return 'live_duplicate.charlink_hook_duplicate_1'


@hooks.register('charlink')
def register_charlink_hook():
    return 'live_duplicate.charlink_hook_duplicate_2'
