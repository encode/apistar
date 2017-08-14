import os
import tempfile

import pytest

from apistar import App, exceptions
from apistar.components import Component
from apistar.components.console import BufferConsole
from apistar.interfaces import Console

components = [
    Component(Console, init=BufferConsole)
]
app = App(components=components)


def test_new():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        app.main(['new', 'myproject', '--layout', 'minimal'], standalone_mode=False)
        assert os.path.exists('myproject')
        assert os.path.exists(os.path.join('myproject', 'app.py'))
        assert os.path.exists(os.path.join('myproject', 'tests.py'))
    assert app.console.buffer.splitlines() == [
        'myproject/app.py',
        'myproject/tests.py'
    ]


def test_do_not_overwrite_existing_project():
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        app.main(['new', 'myproject', '--layout', 'minimal'], standalone_mode=False)
        with pytest.raises(exceptions.CommandLineError):
            app.main(['new', 'myproject', '--layout', 'minimal'], standalone_mode=False)
