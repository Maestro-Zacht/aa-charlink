# AllianceAuth CharLink

[![PyPI](https://img.shields.io/pypi/v/aa-charlink)](https://pypi.org/project/aa-charlink/)

A simple app for AllianceAuth that allows users to link each character to all the AllianceAuth apps with only 1 login action.

## Overview

### Basic usage

1. Select which app you want to link your character to
   ![Charlink Homepage](https://raw.githubusercontent.com/Maestro-Zacht/aa-charlink/e5dd9519cd3772b19505f4ca4b02771774d2a695/docs/images/charlink_homepage.png)
2. Login on CPP site
3. Character linked to the selected apps
   ![Success](https://raw.githubusercontent.com/Maestro-Zacht/aa-charlink/e5dd9519cd3772b19505f4ca4b02771774d2a695/docs/images/charlink_success.png)

### Auditing

Users with the appropriate permission (see [permissions](#permissions)) can audit the linked characters of the users of their corporation, alliance or auth state. A link will appear on top of the main page of the app and will redirect to a page with a table of all the linked characters of the users of the selected corporation.

A user can be audited by clicking on the link on the `Main Character` column.

NEW: Users can now audit the apps they have access to. Select the app you want to audit from the dropdown menu in the audit page.

## Installation

1. Install the app with

   ```shell
   pip install aa-charlink
   ```

2. Add `'charlink',` to your `INSTALLED_APPS` in `local.py`
3. Run migrations and collectstatic

   ```shell
   python manage.py migrate
   python manage.py collectstatic
   ```

## Current apps

I've opened an [issue](https://github.com/Maestro-Zacht/aa-charlink/issues/1) to track the apps that have a default integration in CharLink and the WIPs. If you want another app to be supported, please comment on the issue, reach me on the [AllianceAuth discord server](https://discord.gg/fjnHAmk) or ask the developer of the app to implement an [integration via hook](#hook-integration).

## Hook integration

From version 1.1.0, CharLink supports hook integration. If you want to integrate your app with CharLink, you need to register a hook in the `auth_hooks.py` file:

```python
@hooks.register('charlink')
def register_charlink_hook():
   return 'testauth.testapp.charlink_hook'
```

The hook has to return a string with the import path of the module containing the app integration. The module must contain a variable called `app_import` which is an instance of `charlink.app_imports.utils.AppImport`. You can find the documentation of the class in the [`utils.py`](./charlink/app_imports/utils.py) and some examples in the [imports folder](./charlink/imports).

## Settings

| Name                   | Description                                                                         | Default |
| ---------------------- | ----------------------------------------------------------------------------------- | ------- |
| `CHARLINK_IGNORE_APPS` | List of apps to ignore. Use the name of the app as it is called in `INSTALLED_APPS` | `[]`    |

## Permissions

| Name                     | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| `charlink.view_corp`     | Can view linked character of members of their corporation. |
| `charlink.view_alliance` | Can view linked character of members of their alliance.    |
| `charlink.view_state`    | Can view linked character of members of their auth state.  |

## Login page url

If you want to setup a template override to link the "Add character" button to the login page of this package, set the `a` element to:

```html
<a href="{% url 'charlink:index' %}" class="btn btn-block btn-info" title="Add Character">{% translate 'Add Character' %}</a>
```

## Known issues

- For AFAT is not possible to check if the added character has a token which is still valid, it only checks if the character has ever added a token with the required scopes.
