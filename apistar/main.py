"""
The `apistar` command line client.
"""
import importlib.util
import os
import sys

import click

from apistar.app import App
from apistar.exceptions import ConfigurationError

sys.dont_write_bytecode = True


def get_app_path() -> str:
    return os.path.join(os.getcwd(), 'app.py')


def get_current_app() -> App:
    app_path = get_app_path()
    if not os.path.exists(app_path):
        raise ConfigurationError("No app.py module exists.")

    spec = importlib.util.spec_from_file_location("app", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'app'):
        raise ConfigurationError("The app.py module did not contain an 'app' variable.")

    app = module.app  # type: ignore
    return app


def setup_pythonpath() -> None:
    cwd = os.getcwd()
    sys.path.insert(0, cwd)


def main() -> None:  # pragma: no cover
    setup_pythonpath()
    app_path = get_app_path()
    if os.path.exists(app_path):
        app = get_current_app()
    else:
        app = App()

    try:
        app.click()
    except ConfigurationError as exc:
        click.echo(str(exc))
        sys.exit(1)


if __name__ == '__main__':  # pragma: no cover
    main()
