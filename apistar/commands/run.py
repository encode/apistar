import click
from werkzeug.serving import is_running_from_reloader, run_simple

from apistar import schema


class Host(schema.String):
    description = 'The host of the webserver.'
    default = 'localhost'


class Port(schema.Integer):
    description = 'The port of the webserver.'
    default = 8080


class NoDebugger(schema.Boolean):
    description = 'Turn off the Werkzeug debugger (on by default)'
    default = False


def run(host: Host, port: Port, no_debugger: NoDebugger) -> None:  # pragma: nocover
    """
    Run the current app.
    """
    from apistar.cli import get_current_app
    app = get_current_app()

    try:
        if not is_running_from_reloader():
            click.echo('Starting up...')
        run_simple(host, port, app.wsgi, use_reloader=True, use_debugger=(not no_debugger), extra_files=['app.py'])
    except KeyboardInterrupt:
        pass
