import json
import sys
import typing

import werkzeug

from apistar import commands, exceptions, http
from apistar.cli import Command
from apistar.components import (
    commandline, dependency, router, schema, statics, templates, wsgi
)
from apistar.interfaces import (
    CommandConfig, CommandLineClient, KeywordArgs, RouteConfig, Router, Schema,
    Settings, StaticFiles, Templates, WSGICallable, WSGIEnviron
)


class App(WSGICallable):
    INJECTOR_CLS = dependency.DependencyInjector

    BUILTIN_COMMANDS = [
        Command('run', commands.run),
        Command('schema', commands.schema)
    ]

    BUILTIN_COMPONENTS = {
        Schema: schema.CoreAPISchema,
        Templates: templates.Jinja2Templates,
        StaticFiles: statics.WhiteNoiseStaticFiles,
        Router: router.WerkzeugRouter,
        CommandLineClient: commandline.ArgParseCommandLineClient
    }  # type: typing.Dict[type, typing.Callable]

    WSGI_COMPONENTS = {
        http.Method: wsgi.get_method,
        http.URL: wsgi.get_url,
        http.Scheme: wsgi.get_scheme,
        http.Host: wsgi.get_host,
        http.Port: wsgi.get_port,
        http.Path: wsgi.get_path,
        http.Headers: wsgi.get_headers,
        http.Header: wsgi.get_header,
        http.QueryString: wsgi.get_querystring,
        http.QueryParams: wsgi.get_queryparams,
        http.QueryParam: wsgi.get_queryparam,
        http.Body: wsgi.get_body,
        http.RequestData: wsgi.get_request_data,
    }  # type: typing.Dict[type, typing.Callable]

    def __init__(self,
                 routes: RouteConfig=None,
                 commands: CommandConfig=None,
                 components: typing.Dict[type, typing.Callable]=None,
                 settings: typing.Dict[str, typing.Any]=None) -> None:
        if routes is None:
            routes = []
        if commands is None:
            commands = []
        if components is None:
            components = {}
        if settings is None:
            settings = {}

        commands = [*self.BUILTIN_COMMANDS, *commands]
        components = {**self.BUILTIN_COMPONENTS, **components}

        self.routes = routes
        self.commands = commands
        self.settings = settings

        components, initial_state = self._preload_components(components)

        self.router = initial_state[Router]
        self.commandline = initial_state[CommandLineClient]
        self._setup_wsgi_injector(components, initial_state)
        self._setup_cli_injector(components, initial_state)

    def _preload_components(self,
                            components: typing.Dict[type, typing.Callable]) -> typing.Tuple[
                                                                                    typing.Dict[type, typing.Callable],
                                                                                    typing.Dict[type, typing.Any]
                                                                                ]:
        """
        Create any components that can be preloaded at the point of
        instantiating the app. This ensures that the dependency injection
        will not need to re-create these on every incoming request or
        command-line invocation.

        Args:
            components: The components that have been configured for this app.

        Return:
            A tuple of the components that could not be preloaded,
            and the initial state, which may include preloaded components.
        """
        initial_state = {
            RouteConfig: self.routes,
            CommandConfig: self.commands,
            Settings: self.settings,
            WSGICallable: self,
        }
        injector = self.INJECTOR_CLS(components, initial_state)

        for interface, func in list(components.items()):
            try:
                component = injector.run(func)
            except exceptions.CouldNotResolveDependency:
                continue
            del components[interface]
            initial_state[interface] = component
            injector = self.INJECTOR_CLS(components, initial_state)

        return (components, initial_state)

    def _setup_wsgi_injector(self,
                             components: typing.Dict[type, typing.Callable],
                             initial_state: typing.Dict[type, typing.Any]) -> None:
        """
        Create the dependency injector for running handlers in response to
        incoming HTTP requests.

        Args:
            components: Any components that are created per-request.
            initial_state: Any preloaded components and other initial state.
        """
        self.wsgi_injector = self.INJECTOR_CLS(
            components={**self.WSGI_COMPONENTS, **components},
            initial_state=initial_state,
            required_state={
                WSGIEnviron: 'wsgi_environ',
                KeywordArgs: 'kwargs',
                Exception: 'exc'
            },
            resolvers=[dependency.HTTPResolver()]
        )

    def _setup_cli_injector(self,
                            components: typing.Dict[type, typing.Callable],
                            initial_state: typing.Dict[type, typing.Any]) -> None:
        """
        Create the dependency injector for running handlers in response to
        command-line invocation.

        Args:
            components: Any components that are created per-request.
            initial_state: Any preloaded components and other initial state.
        """
        self.cli_injector = self.INJECTOR_CLS(
            components=components,
            initial_state=initial_state,
            required_state={
                KeywordArgs: 'kwargs',
            },
            resolvers=[dependency.CliResolver()]
        )

    def __call__(self,
                 environ: typing.Dict[str, typing.Any],
                 start_response: typing.Callable):
        state = {
            'wsgi_environ': environ,
            'kwargs': None,
            'exc': None
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        try:
            handler, kwargs = self.router.lookup(path, method)
            state['kwargs'] = kwargs
            response = self.wsgi_injector.run(handler, state=state)
            response = self.finalize_response(response)
        except Exception as exc:
            state['exc'] = exc  # type: ignore
            response = self.wsgi_injector.run(self.exception_handler, state=state)
            response = self.finalize_response(response)

        return response(environ, start_response)

    def exception_handler(self, exc: Exception) -> http.Response:
        if isinstance(exc, exceptions.Found):
            return http.Response('', exc.status_code, {'Location': exc.location})

        if isinstance(exc, exceptions.HTTPException):
            if isinstance(exc.detail, str):
                content = {'message': exc.detail}
            else:
                content = exc.detail
            return http.Response(content, exc.status_code, {})

        raise

    def finalize_response(self, response):
        # TODO: We want to remove this in favor of more dynamic response types.
        if isinstance(response, werkzeug.Response):
            return response
        elif isinstance(response, http.Response):
            data, status, headers = response
        else:
            data, status, headers = response, 200, {}

        if data is None:
            content = b''
            content_type = 'text/plain'
        elif isinstance(data, str):
            content = data.encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        elif isinstance(data, bytes):
            content = data
            content_type = 'text/html; charset=utf-8'
        else:
            content = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if not content and status == 200:
            status = 204
            content_type = None

        if 'Content-Type' in headers:
            content_type = None

        return werkzeug.Response(content, status, headers, content_type=content_type)

    def main(self,
             args: typing.Sequence[str]=None,
             standalone_mode: bool=True):
        if args is None:  # pragma: nocover
            args = sys.argv[1:]

        state = {}
        try:
            handler, kwargs = self.commandline.parse(args)
            state['kwargs'] = kwargs
            ret = self.cli_injector.run(handler, state=state)
        except exceptions.CommandLineExit as exc:
            ret = exc.message
        except exceptions.CommandLineError as exc:
            if standalone_mode:  # pragma: nocover
                sys.stderr.write('Error: %s\n' % exc)
                sys.exit(exc.exit_code)
            raise
        except (EOFError, KeyboardInterrupt):  # pragma: nocover
            sys.stderr.write('Aborted!\n')
            sys.exit(1)

        if standalone_mode and ret is not None:  # pragma: nocover
            print(ret)
        return ret
