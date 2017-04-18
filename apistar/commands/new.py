import os
import shutil
import sys

import click

import apistar
from apistar import schema


APISTAR_PACKAGE_DIR = os.path.dirname(apistar.__file__)
LAYOUTS_DIR = os.path.join(APISTAR_PACKAGE_DIR, 'layouts')
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
