import os
import shutil
import sys

import click
import pytest
from werkzeug.serving import is_running_from_reloader, run_simple

import apistar
from apistar import schema
from apistar.exceptions import ConfigurationError

ROOT_DIR = os.path.dirname(apistar.__file__)
LAYOUTS_DIR = os.path.join(ROOT_DIR, 'layouts')
LAYOUT_CHOICES = os.listdir(LAYOUTS_DIR)


class TargetDir(schema.String):
    pass


class Layout(schema.String):
    description = 'Select the project layout to use.'
    default = 'standard'
    choices = LAYOUT_CHOICES


class Force(schema.Boolean):
    description = 'Overwrite any existing project files.'
    default = False


def new(target_dir: TargetDir, layout: Layout, force: Force):
    """
    Create a new project in TARGET_DIR.
    """
    source_dir = os.path.join(LAYOUTS_DIR, layout)

    copy_paths = []
    for dir_path, dirs, filenames in os.walk(source_dir):
        for filename in filenames:
            source_path = os.path.join(dir_path, filename)
            rel_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, rel_path)
            if os.path.exists(target_path) and not force:
                click.echo('Project files already exist. Use `-f` to overwrite.')
                sys.exit(1)
            copy_paths.append((source_path, target_path))

    for source_path, target_path in copy_paths:
        click.echo(target_path)
        parent = os.path.dirname(target_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy(source_path, target_path)


class Host(schema.String):
    description = 'The host of the webserver.'
    default = 'localhost'


class Port(schema.Integer):
    description = 'The port of the webserver.'
    default = 8080


def run(host: Host, port: Port):  # pragma: nocover
    """
    Run the current app.
    """
    from apistar.main import get_current_app
    app = get_current_app()

    try:
        if not is_running_from_reloader():
            click.echo('Starting up...')
        run_simple(host, port, app.wsgi, use_reloader=True, use_debugger=True, extra_files=['app.py'])
    except KeyboardInterrupt:
        pass


def test():
    """
    Run the test suite.
    """
    file_or_dir = []
    if os.path.exists('tests'):
        file_or_dir.append('tests')
    if os.path.exists('tests.py'):
        file_or_dir.append('tests.py')
    if not file_or_dir:
        raise ConfigurationError("No 'tests/' directory or 'tests.py' module.")

    exitcode = pytest.main(list(file_or_dir))
    if exitcode:
        sys.exit(exitcode)
