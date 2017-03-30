from apistar import commands, routing
from collections import OrderedDict
import click


built_in_commands = [
    commands.new,
    commands.run,
    commands.test,
]


class App(object):
    def __init__(self, routes=None, commands=None):
        routes = [] if (routes is None) else routes
        commands = [] if (commands is None) else commands

        self.routes = routes
        self.commands = built_in_commands + commands

        self.router = routing.Router(self.routes)
        self.wsgi = get_wsgi_server(app=self)
        self.click = get_click_client(app=self)


def get_wsgi_server(app):
    lookup = app.router.lookup
    lookup_cache = OrderedDict()  # FIFO Cache for URL lookups.
    max_cache = 10000

    # Pre-fill the lookup cache for URLs without path arguments.
    for path, method, view in app.router.routes:
        if '{' not in path:
            key = method.upper() + ' ' + path
            lookup_cache[key] = lookup(path, method)

    def func(environ, start_response):
        method = environ['REQUEST_METHOD']
        path = environ['PATH_INFO']
        lookup_key = method + ' ' + path
        state = {
            'wsgi_environ': environ,
            'app': app,
            'method': method,
            'path': path,
        }

        try:
            (state['view'], pipeline, state['url_path_args']) = lookup_cache[lookup_key]
        except KeyError:
            (state['view'], pipeline, state['url_path_args']) = lookup_cache[lookup_key] = lookup(path, method)
            if len(lookup_cache) > max_cache:
                lookup_cache.pop(next(iter(lookup_cache)))

        for function, inputs, output, extra_kwargs in pipeline:
            # Determine the keyword arguments for each step in the pipeline.
            kwargs = {}
            for arg_name, state_key in inputs:
                kwargs[arg_name] = state[state_key]
            if extra_kwargs is not None:
                kwargs.update(extra_kwargs)

            # Call the function for each step in the pipeline.
            if output is None:
                function(**kwargs)
            else:
                state[output] = function(**kwargs)

        wsgi_response = state['wsgi_response']
        start_response(wsgi_response.status, wsgi_response.headers)
        return wsgi_response.iterator

    return func


def get_click_client(app):
    @click.group(invoke_without_command=True, help='API Star')
    @click.option('--version', is_flag=True, help='Display the `apistar` version number.')
    @click.pass_context
    def client(ctx, version):
        if ctx.invoked_subcommand is not None:
            return

        if version:
            from apistar import __version__
            click.echo(__version__)
        else:
            click.echo(ctx.get_help())

    for command in app.commands:
        client.add_command(command)

    return client
