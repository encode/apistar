"""
The `apistar` command line client.
"""
import importlib.util
import os
import sys

from apistar import exceptions
from apistar.frameworks.cli import CliApp
from apistar.interfaces import App


def load_app(filepath) -> App:
    folder = os.path.dirname(filepath)
    sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location("app", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = getattr(module, 'app', None)
    if app is None:
        msg = "The 'app.py' module did not contain an 'app' variable."
        raise exceptions.ConfigurationError(msg)
    if not isinstance(app, App):
        msg = "The 'app' variable in 'app.py' is not an App instance."
        raise exceptions.ConfigurationError(msg)
    return app


def default_app() -> App:
    return CliApp()


def main() -> None:  # pragma: nocover
    filepath = os.getenv('APISTAR_APP', os.path.join(os.getcwd(), 'app.py'))
    if os.path.isfile(filepath):
        app = load_app(filepath)
    else:
        app = default_app()
    app.main()
