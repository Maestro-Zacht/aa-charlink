# AllianceAuth CharLink

[![PyPI](https://img.shields.io/pypi/v/aa-charlink)](https://pypi.org/project/aa-charlink/)

A simple app for AllianceAuth that allows users to link each character to all the AllianceAuth apps with only 1 login action.

## Overview

1. Select which app you want to link your character to
   ![Overview](https://raw.githubusercontent.com/Maestro-Zacht/aa-charlink/main/docs/images/charlink_homepage.png)
2. Login on CPP site
3. Character linked to the selected apps
   ![Success](https://raw.githubusercontent.com/Maestro-Zacht/aa-charlink/main/docs/images/charlink_success.png)

## Installation

1. Install the app with

   ```shell
   pip install aa-charlink
   ```

2. Add `'charlink',` to your `INSTALLED_APPS` in `local.py`

## Current apps

I've opened an [issue](https://github.com/Maestro-Zacht/aa-charlink/issues/1) to track the current apps that are implemented in CharLink and the WIPs. If you want another app to be supported, please comment on the issue or reach me on the [AllianceAuth discord server](https://discord.gg/fjnHAmk).

## Settings

| Name                   | Description                                                                         | Default |
| ---------------------- | ----------------------------------------------------------------------------------- | ------- |
| `CHARLINK_IGNORE_APPS` | List of apps to ignore. Use the name of the app as it is called in `INSTALLED_APPS` | `[]`    |
