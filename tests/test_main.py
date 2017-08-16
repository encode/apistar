import os
import tempfile

import pytest

from apistar import exceptions
from apistar.interfaces import App
from apistar.main import default_app, load_app


def test_default_app():
    default = default_app()
    assert isinstance(default, App)


def test_load_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        app = default_app()
        app.main(['new', '.'], standalone_mode=False)
        loaded = load_app()
        assert isinstance(loaded, App)


def test_load_missing_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('')
        with pytest.raises(exceptions.ConfigurationError):
            load_app()


def test_load_invalid_app():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        with open('app.py', 'w') as app_file:
            app_file.write('app = 123\n')
        with pytest.raises(exceptions.ConfigurationError):
            load_app()
