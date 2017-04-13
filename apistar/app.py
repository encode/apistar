from collections import OrderedDict

import click

from apistar import commands, routing


class App(object):
    built_in_commands = (
        commands.new,
        commands.run,
        commands.test,
    )

    def __init__(self, routes=None, commands=None, db_engine_config=None):
        routes = [] if (routes is None) else routes
        commands = [] if (commands is None) else commands

        self.routes = routes
        self.commands = list(self.built_in_commands) + commands

        self.router = routing.Router(self.routes)
        self.wsgi = get_wsgi_server(app=self)
        self.click = get_click_client(app=self)

        # testing sql alchamy
        self.db_backend = None

        if db_engine_config:
            # this could be moved into a plugin or external backend?
            if db_engine_config.get('TYPE') == "SQLALCHEMY":

                if 'DB_URL' in db_engine_config:

                    from sqlalchemy import create_engine
                    from sqlalchemy.orm import sessionmaker

                    engine = create_engine(
                        db_engine_config['DB_URL'],
                        echo=True,
                        echo_pool=True,
                        pool_size=db_engine_config.get('DB_POOL_SIZE', 5)
                    )
                    session_class = sessionmaker(bind=engine)

                    self.db_backend = DBBackend(engine=engine, session_class=session_class)

                    if 'METADATA' in db_engine_config:
                        # put in command
                        db_engine_config['METADATA'].create_all(self.db_backend.engine)


class DBBackend(object):
    __slots__ = ('engine', 'session_class')

    def __init__(self, engine, session_class):
        self.engine = engine
        self.session_class = session_class


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
            'db_backend': app.db_backend,
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
