from apistar import components, commands, routing
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

        self.router = routing.get_router(self.routes)
        self.wsgi = get_wsgi_server(app=self)
        self.click = get_click_client(app=self)


def get_wsgi_server(app):
    lookup = app.router

    def func(environ, start_response):
        method = environ['REQUEST_METHOD']
        path = environ['PATH_INFO']
        state = {
            'wsgi_environ': environ,
            'app': app,
            'method': method,
            'path': path,
        }
        (state['view'], pipeline) = lookup(path, method)
        for function, inputs, output in pipeline:
            kwargs = {
                func_key: state[state_key]
                for func_key, state_key in inputs
            }
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
