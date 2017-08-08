import werkzeug

from apistar.interfaces import WSGICallable


def run(app: WSGICallable,
        host: str='127.0.0.1',
        port: int=8080,
        debug=True,
        reloader=True) -> None:  # pragma: nocover
    """
    Run the development server.

    Args:
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
