"""
              _    ____ ___   ____  _
 __/\__      / \  |  _ \_ _| / ___|| |_ __ _ _ __    __/\__
 \    /     / _ \ | |_) | |  \___ \| __/ _` | '__|   \    /
 /_  _\    / ___ \|  __/| |   ___) | || (_| | |      /_  _\
   \/     /_/   \_\_|  |___| |____/ \__\__,_|_|        \/
"""

from pathlib import Path

import toml

from apistar.client import Client
from apistar.document import Document, Field, Link, Section
from apistar.main import main
from apistar.server import App, ASyncApp, Component, Include, Route
from apistar.test import TestClient


def get_version():
    path = Path(__file__).resolve().parents[1] / 'pyproject.toml'
    pyproject = toml.loads(open(str(path)).read())
    return pyproject['tool']['poetry']['version']


__version__ = get_version()
__all__ = [
    'App', 'ASyncApp', 'Client', 'Component', 'Document', 'Section', 'Link', 'Field',
    'Route', 'Include', 'TestClient', 'http', 'main'
]
