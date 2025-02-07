from app_utils.app_settings import clean_setting

CHARLINK_IGNORE_APPS = set(clean_setting('CHARLINK_IGNORE_APPS', []))
