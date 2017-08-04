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
    CommandConfig, CommandLineClient, Injector, KeywordArgs, RouteConfig,
    Router, Schema, Settings, StaticFiles, Templates, WSGICallable,
    WSGIEnviron
)


class App(WSGICallable):
    BUILTIN_COMMANDS = [
        Command('run', commands.run),
        Command('schema', commands.schema)
    ]

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

    FRAMEWORK_COMPONENTS = {
        Schema: schema.CoreAPISchema,
        Templates: templates.Jinja2Templates,
        StaticFiles: statics.WhiteNoiseStaticFiles,
        Router: router.WerkzeugRouter,
        Injector: dependency.DependencyInjector,
        CommandLineClient: commandline.ArgParseCommandLineClient
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
        components = {**self.FRAMEWORK_COMPONENTS, **components}
        injector_cls = components.pop(Injector)

        self.routes = routes
        self.settings = settings
        self.router = components[Router](routes)
        self.commandline = components[CommandLineClient](commands)

        self.wsgi_injector = injector_cls(
            components={**self.WSGI_COMPONENTS, **components},
            initial_state={
                RouteConfig: routes,
                CommandConfig: commands,
                Settings: settings,
                WSGICallable: self,
            },
            required_state={
                WSGIEnviron: 'wsgi_environ',
                KeywordArgs: 'kwargs',
                Exception: 'exc'
            },
            resolvers=[dependency.HTTPResolver()]
        )
        self.cli_injector = injector_cls(
            components=components,
            initial_state={
                RouteConfig: routes,
                CommandConfig: commands,
                Settings: settings,
                WSGICallable: self,
            },
            required_state={
                KeywordArgs: 'kwargs',
            },
            resolvers=[dependency.CliResolver()]
        )

    def __call__(self, environ: typing.Dict[str, typing.Any], start_response: typing.Callable):
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
