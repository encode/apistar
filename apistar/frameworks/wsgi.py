import json
import typing

from werkzeug.http import HTTP_STATUS_CODES

from apistar import commands, exceptions, http
from apistar.cli import Command
from apistar.components import (
    commandline, console, dependency, router, schema, statics, templates, wsgi
)
from apistar.frameworks.cli import CliApp
from apistar.interfaces import (
    CommandLineClient, Console, Injector, KeywordArgs, Router, Schema,
    StaticFiles, Templates, WSGIEnviron
)

STATUS_TEXT = {
    code: "%d %s" % (code, msg)
    for code, msg in HTTP_STATUS_CODES.items()
}


class WSGIApp(CliApp):
    INJECTOR_CLS = dependency.DependencyInjector

    BUILTIN_COMMANDS = [
        Command('new', commands.new),
        Command('run', commands.run),
        Command('schema', commands.schema)
    ]

    BUILTIN_COMPONENTS = {
        Schema: schema.CoreAPISchema,
        Templates: templates.Jinja2Templates,
        StaticFiles: statics.WhiteNoiseStaticFiles,
        Router: router.WerkzeugRouter,
        CommandLineClient: commandline.ArgParseCommandLineClient,
        Console: console.PrintConsole
    }  # type: typing.Dict[type, typing.Callable]

    HTTP_COMPONENTS = {
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Setup everything that we need in order to run `self.__call__()`
        self.router = self.preloaded_state[Router]
        self.http_injector = self.create_http_injector()

    def create_http_injector(self) -> Injector:
        """
        Create the dependency injector for running handlers in response to
        incoming HTTP requests.

        Args:
            components: Any components that are created per-request.
            initial_state: Any preloaded components and other initial state.
        """
        return self.INJECTOR_CLS(
            components={**self.HTTP_COMPONENTS, **self.components},
            initial_state=self.preloaded_state,
            required_state={
                WSGIEnviron: 'wsgi_environ',
                KeywordArgs: 'kwargs',
                Exception: 'exc'
            },
            resolvers=[dependency.HTTPResolver()]
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
            response = self.http_injector.run(handler, state=state)
        except Exception as exc:
            state['exc'] = exc  # type: ignore
            response = self.http_injector.run(self.exception_handler, state=state)

        if getattr(response, 'content_type', None) is None:
            response = self.finalize_response(response)

        # Get the WSGI response information, given the Response instance.
        try:
            status_text = STATUS_TEXT[response.status]
        except KeyError:
            status_text = str(response.status)

        headers = list(response.headers.items())
        headers.append(('content-type', response.content_type))

        if isinstance(response.content, (bytes, str)):
            content = [response.content]
        else:
            content = response.content

        # Return the WSGI response.
        start_response(status_text, headers)
        return content

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
        if isinstance(response, http.Response):
            data, status, headers, content_type = response
        else:
            data, status, headers, content_type = response, 200, {}, None

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
            content_type = 'text/plain'

        return http.Response(content, status, headers, content_type)
