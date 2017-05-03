import click
from werkzeug.serving import is_running_from_reloader, run_simple

from apistar import schema


class Host(schema.String):
    description = 'The host of the webserver.'
    default = 'localhost'


class Port(schema.Integer):
    description = 'The port of the webserver.'
    default = 8080


def run(host: Host, port: Port) -> None:  # pragma: nocover
    """
    Run the current app.
    """
    from apistar.main import get_current_app
    app = get_current_app()

    try:
        if not is_running_from_reloader():
            click.echo('Starting up...')
        run_simple(host, port, app.wsgi, use_reloader=True, use_debugger=True, extra_files=['app.py'])
    except KeyboardInterrupt:
        pass
