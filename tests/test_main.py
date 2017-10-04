import os
import tempfile

import pytest

from apistar import exceptions, get_current_app
from apistar.frameworks.cli import CliApp
from apistar.interfaces import App


def test_get_current_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        app = CliApp()
        app.main(['new', '.'], standalone_mode=False)
        loaded = get_current_app(use_cache=False)
        assert isinstance(loaded, App)


def test_get_missing_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('')
        with pytest.raises(exceptions.ConfigurationError):
            get_current_app(use_cache=False)


def test_get_invalid_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('app = 123\n')
        with pytest.raises(exceptions.ConfigurationError):
            get_current_app(use_cache=False)
