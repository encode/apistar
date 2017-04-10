"""
The `apistar` command line client.
"""
import importlib.util
import os
import sys

import click

from apistar import App
from apistar.exceptions import ConfigurationError, NoCurrentApp

sys.dont_write_bytecode = True


def get_current_app():
    app_path = os.path.join(os.getcwd(), 'app.py')
    if not os.path.exists(app_path):
        raise NoCurrentApp("No app.py module exists.")

    spec = importlib.util.spec_from_file_location("app", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'app'):
        raise ConfigurationError("The app.py module did not contain an 'app' variable.")

    app = module.app
    return app


def setup_environ():
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        for line in open(env_path, 'r'):
            variable, sep, value = line.partition('=')
            variable = variable.strip()
            value = value.strip()
            if variable:
                os.environ[variable] = value


def setup_pythonpath():
    cwd = os.getcwd()
    sys.path.insert(0, cwd)


def main():  # pragma: no cover
    setup_pythonpath()
    setup_environ()
    try:
        app = get_current_app()
    except NoCurrentApp:
        app = App()

    try:
        app.click()
    except (NoCurrentApp, ConfigurationError) as exc:
        click.echo(str(exc))
        sys.exit(1)


if __name__ == '__main__':  # pragma: no cover
    main()
