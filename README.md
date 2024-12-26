# AllianceAuth CharLink

[![PyPI](https://img.shields.io/pypi/v/aa-charlink)](https://pypi.org/project/aa-charlink/)

![EvE Partner](https://raw.githubusercontent.com/Maestro-Zacht/aa-charlink/503fac8d44c7c40ea8489da6519f94219446d1e5/docs/images/eve_partner.jpg)

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

App Audit: Users can now audit character based on the apps they have access to. Select the app you want to audit from the dropdown menu in the audit page.
Admin App status: users with `is_superuser` can now see the list of imported apps and the ones with issues with the import.

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

| Name                   | Description                                                                                                                                                                                                                                     | Default |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `CHARLINK_IGNORE_APPS` | List of apps to ignore. Use the name of the app as it is called in `INSTALLED_APPS` if you want to ignore all the entries for that app, or any of the options in the [following section]( #ignoring-single-entries) for ignoring a single entry | `[]`    |

### Ignoring single entries

The following apps have more than 1 entry and you can ignore individual entries by adding the relative option below:

- `AllianceAuth Contacts`
  - `Alliance Contacts`: `aa_contacts.alliance`
  - `Corporation Contacts`: `aa_contacts.corporation`
- `Corptools`
  - `Character Audit`: `corptools.default`
  - `Corporation Audit`: `corptools.structures`
- `MiningTaxes`
  - `Mining Taxes`: `miningtaxes.default`
  - `Mining Taxes Admin`: `miningtaxes.admin`
- `AFAT`
  - `AFAT Read Fleet`: `afat.readfleet`
  - `AFAT Click Tracking`: `afat.clickfat`
- `Market Manager`
  - `Market Manager - Character Login`: `marketmanager.character`
  - `Market Manager - Corporation Login`: `marketmanager.corporation`

## Permissions

| Name                     | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| `charlink.view_corp`     | Can view linked character of members of their corporation. |
| `charlink.view_alliance` | Can view linked character of members of their alliance.    |
| `charlink.view_state`    | Can view linked character of members of their auth state.  |

## Login page url

If you want to setup a template override to link the "Add character" button to the login page of this package, set the `a` element to:

```html
<a href="{% url 'charlink:index' %}" class="btn btn-primary flex-fill m-1" title="{% translate 'Add Character' %}">
      <span class="d-md-inline m-2">{% translate 'Add Character' %}</span>
</a>

```

## Known issues

- For AFAT is not possible to check if the added character has a token which is still valid, it only checks if the character has ever added a token with the required scopes.
