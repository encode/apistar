import os
import shutil
import sys

import click
import pytest
from werkzeug.serving import is_running_from_reloader, run_simple

import apistar
from apistar.exceptions import ConfigurationError

ROOT_DIR = os.path.dirname(apistar.__file__)
LAYOUTS_DIR = os.path.join(ROOT_DIR, 'layouts')
LAYOUT_CHOICES = os.listdir(LAYOUTS_DIR)


@click.command(help='Create a new project in TARGET_DIR.')
@click.argument('target_dir', default='')
@click.option('-l', '--layout', type=click.Choice(LAYOUT_CHOICES), default='standard',
              help='Select the project layout to use.')
@click.option('-f', '--force', is_flag=True, help='Overwrite any existing project files.')
def new(target_dir, layout, force):
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
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        shutil.copy(source_path, target_path)


@click.command(help='Run the current app.')
@click.option('--host', '-h', default='localhost', type=str, help='The host of the webserver.')
@click.option('--port', '-p', default=8080, type=int, help='The port of the webserver.')
def run(host, port):  # pragma: nocover
    from apistar.main import get_current_app
    app = get_current_app()

    try:
        if not is_running_from_reloader():
            click.echo('Starting up...')
        run_simple(host, port, app.wsgi, use_reloader=True, use_debugger=True, extra_files=['app.py'])
    except KeyboardInterrupt:
        pass


@click.command(help='Run the test suite.')
@click.argument('file_or_dir', nargs=-1)
def test(file_or_dir):
    if not file_or_dir:
        file_or_dir = []
        if os.path.exists('tests'):
            file_or_dir.append('tests')
        if os.path.exists('tests.py'):
            file_or_dir.append('tests.py')
        if not file_or_dir:
            raise ConfigurationError("No 'tests/' directory or 'tests.py' module.")

    os.environ['APISTAR_TEST'] = 'true'
    exitcode = pytest.main(list(file_or_dir))
    if exitcode:
        sys.exit(exitcode)
