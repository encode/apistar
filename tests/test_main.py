import os
import tempfile

import pytest

from apistar import exceptions, load_app
from apistar.frameworks.cli import CliApp
from apistar.interfaces import App


def test_load_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        app = CliApp()
        app.main(['new', '.'], standalone_mode=False)
        loaded = load_app(use_cache=False)
        assert isinstance(loaded, App)


def test_load_missing_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('')
        with pytest.raises(exceptions.ConfigurationError):
            load_app(use_cache=False)


def test_load_invalid_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('app = 123\n')
        with pytest.raises(exceptions.ConfigurationError):
            load_app(use_cache=False)
