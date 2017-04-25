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
    if 'APISTAR_APP_PATH' in os.environ:
        return os.environ['APISTAR_APP_PATH']
    elif os.path.exists('app.py'):
        return 'app.py'
    return None


def get_app_instance() -> str:
    if 'APISTAR_APP_INSTANCE' in os.environ:
        return os.environ['APISTAR_APP_INSTANCE']
    return 'app'


def get_env_path() -> str:
    if 'APISTAR_ENV_FILE' in os.environ:
        return os.environ['APISTAR_ENV_FILE']
    elif os.path.exists('.env'):
        return '.env'
    return None


def get_current_app() -> App:
    app_path = get_app_path()
    app_instance = get_app_instance()
    if app_path is None:
        raise ConfigurationError('No app is loaded.')
    return load_app(app_path, app_instance)


def load_app(app_path: str, app_instance: str) -> App:
    if not os.path.exists(app_path):
        msg = "Module '%s' does not exist."
        raise ConfigurationError(msg % app_path)

    spec = importlib.util.spec_from_file_location("app", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = getattr(module, app_instance, None)
    if app is None:
        msg = "Module '%s' does not contain an '%s' attribute."
        raise ConfigurationError(msg % (app_path, app_instance))

    return app


def setup_pythonpath() -> None:
    cwd = os.getcwd()
    sys.path.insert(0, cwd)


def setup_environ(env_path: str) -> None:
    if not os.path.exists(env_path):
        msg = "Environment file '%s' does not exist."
        raise ConfigurationError(msg % env_path)

    for line in open(env_path, 'r'):
        variable, sep, value = line.partition('=')
        variable = variable.strip()
        value = value.strip()
        if variable:
            os.environ[variable] = value


def main() -> None:  # pragma: no cover
    setup_pythonpath()

    env_path = get_env_path()
    if env_path:
        setup_environ(env_path)

    app_path = get_app_path()
    if app_path is None:
        app = App()
    else:
        app = get_current_app()

    try:
        app.click()
    except ConfigurationError as exc:
        click.echo(str(exc))
        sys.exit(1)


if __name__ == '__main__':  # pragma: no cover
    main()
