import apistar
import click
import os
import pytest
import shutil
import sys
from wsgiref.simple_server import make_server


ROOT_DIR = os.path.dirname(apistar.__file__)
PROJECT_TEMPLATES_DIR = os.path.join(ROOT_DIR, 'project_templates')
PROJECT_TEMPLATE_CHOICES = os.listdir(PROJECT_TEMPLATES_DIR)


@click.command(help='Create a new project in TARGET_DIR.')
@click.argument('target_dir')
@click.option('--template', type=click.Choice(PROJECT_TEMPLATE_CHOICES), default='standard', help='Select the project template to use.')
def new(target_dir, template):
    source_dir = os.path.join(PROJECT_TEMPLATES_DIR, template)
    shutil.copytree(source_dir, target_dir)
    for dir_path, dirs, files in os.walk(source_dir):
        for file in files:
            abs_path = os.path.join(dir_path, file)
            rel_path = os.path.relpath(abs_path, source_dir)
            target_path = os.path.join(target_dir, rel_path)
            click.echo(target_path)


@click.command(help='Run the current app.')
def run():
    from apistar.main import get_current_app
    app = get_current_app()
    try:
        click.echo('Running at http://localhost:8080/')
        make_server('', 8080, app.wsgi).serve_forever()
    except KeyboardInterrupt:
        pass


@click.command(help='Run the test suite.')
@click.argument('file_or_dir', nargs=-1)
def test(file_or_dir):
    if not file_or_dir:
        if os.path.exists('tests'):
            file_or_dir = ['tests']
        elif os.path.exists('tests.py'):
            file_or_dir = ['tests.py']
    exitcode = pytest.main(list(file_or_dir))
    if exitcode:
        sys.exit(exitcode)
