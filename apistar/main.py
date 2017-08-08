"""
The `apistar` command line client.
"""
import importlib.util
import os
import sys

from apistar import App, exceptions


def load_app():
    sys.path.insert(0, os.getcwd())
    spec = importlib.util.spec_from_file_location("app", "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = getattr(module, 'app', None)
    if app is None:
        msg = "The app.py module did not contain an 'app' variable."
        raise exceptions.ConfigurationError(msg)
    return app


def default_app():
    return App()


if __name__ == '__main__':  # pragma: nocover
    if os.path.exists('app.py'):
        app = load_app()
    else:
        app = default_app()
    app.main()
