import werkzeug

from apistar.interfaces import App


def run(app: App,
        host: str='127.0.0.1',
        port: int=8080,
        debug: bool=True,
        reloader: bool=True) -> None:  # pragma: nocover
    """
    Run the development server.

    Args:
      app: The application instance, which should be a WSGI callable.
      host: The host of the server.
      port: The port of the server.
      debug: Turn the debugger [on|off].
      reloader: Turn the reloader [on|off].
    """
    options = {
        'use_debugger': debug,
        'use_reloader': reloader,
        'extra_files': ['app.py']
    }
    werkzeug.run_simple(host, port, app, **options)
