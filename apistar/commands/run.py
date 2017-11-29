from apistar.exceptions import ConfigurationError
from apistar.types import AppLoader
from apistar.utils import import_app


def run(app: AppLoader=import_app,
        host: str='127.0.0.1',
        port: int=8080,
        debug: bool=True,
        reloader: bool=True) -> None:  # pragma: nocover
    """
        Run the development server.

        Args:
          app: The application instance.
          host: The host of the server.
          port: The port of the server.
          debug: Turn the debugger [on|off].
          reloader: Turn the reloader [on|off]. Ignored when for ASyncIO apps.
    """
    from apistar.frameworks.wsgi import WSGIApp
    from apistar.frameworks.asyncio import ASyncIOApp

    if isinstance(app, WSGIApp):
        run_wsgi(app, host, port, debug, reloader)
    elif isinstance(app, ASyncIOApp):
        run_asyncio(app, host, port, debug)
    else:
        raise ConfigurationError("Unsupported application type %r" % app)


def run_wsgi(app: AppLoader=import_app,
             host: str='127.0.0.1',
             port: int=8080,
             debug: bool=True,
             reloader: bool=True) -> None:  # pragma: nocover
    """
        Run the WSGI development server.

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


def run_asyncio(app: AppLoader=import_app,
                host: str='127.0.0.1',
                port: int=8080,
                debug: bool=True) -> None:  # pragma: nocover
    """
        Run the ASyncIO development server.

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
