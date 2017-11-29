"""
              _    ____ ___   ____  _
 __/\__      / \  |  _ \_ _| / ___|| |_ __ _ _ __    __/\__
 \    /     / _ \ | |_) | |  \___ \| __/ _` | '__|   \    /
 /_  _\    / ___ \|  __/| |   ___) | || (_| | |      /_  _\
   \/     /_/   \_\_|  |___| |____/ \__\__,_|_|        \/
"""

from apistar import exceptions
from apistar.core import Command, Component, Include, Route, annotate
from apistar.frameworks.cli import CliApp
from apistar.http import Response
from apistar.test import TestClient
from apistar.types import Settings
from apistar.utils import import_app

__version__ = '0.3.9'
__all__ = [
    'annotate', 'exceptions', 'Command', 'Component', 'Response', 'Route',
    'Include', 'Settings', 'TestClient'
]


def main() -> None:
    try:
        app = import_app('app:app')
    except exceptions.ConfigurationError:
        app = CliApp()
    app.main()


def reverse_url(identifier: str, **values) -> str:
    app = import_app('app:app')
    return app.reverse_url(identifier, **values)


def render_template(template_name: str, **context) -> str:
    app = import_app('app:app')
    return app.render_template(template_name, **context)
