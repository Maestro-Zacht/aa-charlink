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

   if you have a baremetal installation, or add the following line to your `requirements.txt` if you are using Docker:

   ```text
   aa-charlink==x.y.z
   ```

   where `x.y.z` is the version you want to install. It is important to pin the version in order to avoid unexpected upgrades and potential breaking changes.

2. Add `'charlink',` to your `INSTALLED_APPS` in `local.py`
3. Run migrations and collectstatic

   If you are using Docker, run:

   ```shell
   auth migrate
   auth collectstatic
   ```

   otherwise

   ```shell
   python manage.py migrate
   python manage.py collectstatic
   ```
4. Check in CharLink Admin page that the apps you want to use are shown correctly and their default selection and visibility are what you want. Some apps have their default selection turned off for a good reason, go to [default selection](#default-selection) for more information.

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

## Ignoring apps

Ignoring apps has been moved from settings to the CharLink Admin page. In order to ignore an app, or one of its login options, click on the related eye button in this page.

## Default selection

From version 1.10.0, login options can have their default selection changed by the admin. This can be done in the CharLink Admin page using the "Default selection" button.

WARNING: Some apps, like Structures, have reportedly causing issues and get the AA instance banned due to the high number of ESI calls they make after linking many chars. In order to avoid this, the default selection of these apps is set to off and a warning is shown in the CharLink Admin page when trying to enable it.

If you want to reset all the default selections to their original value, you can use the management command:

```shell
python manage.py charlink_reset_selections
```

or, if you are using Docker:

```shell
auth charlink_reset_selections
```

## Smartfilters

If [Securegroups](https://github.com/Solar-Helix-Independent-Transport/allianceauth-secure-groups) is installed, CharLink exports the following smartfilters:

- Compliance filter: checks if the user has added all his characters to the selected apps.

## Permissions

| Name                     | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| `charlink.view_corp`     | Can view linked character of members of their corporation. |
| `charlink.view_alliance` | Can view linked character of members of their alliance.    |
| `charlink.view_state`    | Can view linked character of members of their auth state.  |
| `charlink.view_admin`    | Can view CharLink Admin page.                              |

## Login page url

If you want to setup a template override to link the "Add character" button to the login page of this package, set the `a` element to:

```html
<a href="{% url 'charlink:index' %}" class="btn btn-primary flex-fill m-1" title="{% translate 'Add Character' %}">
      <span class="d-md-inline m-2">{% translate 'Add Character' %}</span>
</a>

```

## Known issues

- For AFAT is not possible to check the validity of the added character's token.
