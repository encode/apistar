from apistar.interfaces import App


def run_wsgi(app: App,
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
    import werkzeug

    options = {
        'use_debugger': debug,
        'use_reloader': reloader,
        'extra_files': ['app.py']
    }
    werkzeug.run_simple(host, port, app, **options)


def run_asyncio(app: App,
                host: str='127.0.0.1',
                port: int=8080,
                debug: bool=True):  # pragma: nocover
    """
    Run the development server.

    Args:
      app: The application instance, which should be a UMI callable.
      host: The host of the server.
      port: The port of the server.
      debug: Turn the debugger [on|off].
    """
    import uvicorn

    if debug:
        from uvitools.debug import DebugMiddleware
        app = DebugMiddleware(app, evalex=True)

    uvicorn.run(app, host, port)
