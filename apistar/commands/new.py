import os
import shutil

import apistar
from apistar import exceptions
from apistar.interfaces import Console

APISTAR_PACKAGE_DIR = os.path.dirname(apistar.__file__)
LAYOUTS_DIR = os.path.join(APISTAR_PACKAGE_DIR, 'layouts')
LAYOUT_CHOICES = os.listdir(LAYOUTS_DIR)
IGNORED_DIRECTORIES = ['__pycache__']


def new(console: Console,
        target_dir: str,
        framework: str='wsgi',
        force: bool=False) -> None:
    """
    Create a new project in TARGET_DIR.

    Args:
      console: The console to write output about file creation.
      target_dir: The directory to use when creating the project.
      layout: Select the project layout to use.
      force: Overwrite any existing project files.
    """
    if framework not in ('wsgi', 'asyncio'):
        message = "Invalid framework option. Use 'wsgi' or 'asyncio'."
        raise exceptions.CommandLineError(message)

    source_dir = os.path.join(LAYOUTS_DIR, framework)

    copy_paths = []
    for dir_path, dirs, filenames in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
        for filename in filenames:
            source_path = os.path.join(dir_path, filename)
            rel_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, rel_path)
            if os.path.exists(target_path) and not force:
                message = 'Project files already exist. Use `--force` to overwrite.'
                raise exceptions.CommandLineError(message)
            copy_paths.append((source_path, target_path))

    for source_path, target_path in sorted(copy_paths):
        console.echo(target_path)
        parent = os.path.dirname(target_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy(source_path, target_path)
