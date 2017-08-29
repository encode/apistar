import json
import typing

from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.datastructures import Headers

from apistar import commands, exceptions, http
from apistar.components import (
    commandline, console, dependency, router, schema, statics, templates, wsgi
)
from apistar.core import Command, Component
from apistar.frameworks.cli import CliApp
from apistar.interfaces import (
    CommandLineClient, Console, FileWrapper, Injector, Router, Schema,
    StaticFiles, Templates
)
from apistar.types import KeywordArgs, WSGIEnviron

STATUS_TEXT = {
    code: "%d %s" % (code, msg)
    for code, msg in HTTP_STATUS_CODES.items()
}


class WSGIApp(CliApp):
    INJECTOR_CLS = dependency.DependencyInjector

    BUILTIN_COMMANDS = [
        Command('new', commands.new),
        Command('run', commands.run_wsgi),
        Command('schema', commands.schema),
        Command('test', commands.test)
    ]

    BUILTIN_COMPONENTS = [
        Component(Schema, init=schema.CoreAPISchema),
        Component(Templates, init=templates.Jinja2Templates),
        Component(StaticFiles, init=statics.WhiteNoiseStaticFiles),
        Component(Router, init=router.WerkzeugRouter),
        Component(CommandLineClient, init=commandline.ArgParseCommandLineClient),
        Component(Console, init=console.PrintConsole)
    ]

    HTTP_COMPONENTS = [
        Component(http.Method, init=wsgi.get_method),
        Component(http.URL, init=wsgi.get_url),
        Component(http.Scheme, init=wsgi.get_scheme),
        Component(http.Host, init=wsgi.get_host),
        Component(http.Port, init=wsgi.get_port),
        Component(http.Path, init=wsgi.get_path),
        Component(http.Headers, init=wsgi.get_headers),
        Component(http.Header, init=wsgi.get_header),
        Component(http.QueryString, init=wsgi.get_querystring),
        Component(http.QueryParams, init=wsgi.get_queryparams),
        Component(http.QueryParam, init=wsgi.get_queryparam),
        Component(http.Body, init=wsgi.get_body),
        Component(http.Request, init=http.Request),
        Component(http.RequestData, init=wsgi.get_request_data),
        Component(FileWrapper, init=wsgi.get_file_wrapper)
    ]

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
        http_components = {
            component.cls: component.init
            for component in self.HTTP_COMPONENTS
        }

        return self.INJECTOR_CLS(
            components={**http_components, **self.components},
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
        def add_cors_headers(status, headers, exc_info=None):
            headers = Headers(headers)
            headers.add('Access-Control-Allow-Origin', '*')
            headers.add('Access-Control-Allow-Credentials', True)
            headers.add('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin')
            headers.add('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS, POST, PUT')
            return start_response(status, headers.to_list(), exc_info)
        
        state = {
            'wsgi_environ': environ,
            'kwargs': None,
            'exc': None
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']
        try:
            if method == "OPTIONS":
                add_cors_headers("200 Ok", [("Content-Type", "text/plain")])
                return [b'200 Ok']
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
        headers.append(('Access-Control-Allow-Origin', '*'))
        headers.append(('Access-Control-Allow-Credentials', True))
        headers.append(('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin'))
        headers.append(('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS, POST, PUT'))
        headers.append(('Content-Type', response.content_type))

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

    def finalize_response(self, response: http.Response) -> http.Response:
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
