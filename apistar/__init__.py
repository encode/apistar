"""
              _    ____ ___   ____  _
 __/\__      / \  |  _ \_ _| / ___|| |_ __ _ _ __    __/\__
 \    /     / _ \ | |_) | |  \___ \| __/ _` | '__|   \    /
 /_  _\    / ___ \|  __/| |   ___) | || (_| | |      /_  _\
   \/     /_/   \_\_|  |___| |____/ \__\__,_|_|        \/
"""
import importlib.util
import os
import sys

from apistar import exceptions
from apistar.core import Command, Component, Include, Route, annotate
from apistar.frameworks.cli import CliApp
from apistar.http import Response
from apistar.interfaces import App
from apistar.test import TestClient
from apistar.types import Settings

__version__ = '0.3.6'
__all__ = [
    'annotate', 'exceptions', 'Command', 'Component', 'Response', 'Route',
    'Include', 'Settings', 'TestClient'
]

loaded_app = None


def main() -> None:  # pragma: nocover
    if os.path.exists('app.py'):
        app = load_app()
    else:
        app = CliApp()
    app.main()


def load_app(use_cache=True) -> App:
    global loaded_app

    if loaded_app is not None and use_cache:
        return loaded_app

    sys.path.insert(0, os.getcwd())
    spec = importlib.util.spec_from_file_location("app", "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = getattr(module, 'app', None)
    if app is None:
        msg = "The 'app.py' module did not contain an 'app' variable."
        raise exceptions.ConfigurationError(msg)
    if not isinstance(app, App):
        msg = "The 'app' variable in 'app.py' is not an App instance."
        raise exceptions.ConfigurationError(msg)

    if use_cache:
        loaded_app = app

    return app
