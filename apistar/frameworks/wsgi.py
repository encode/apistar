import typing

from werkzeug.http import HTTP_STATUS_CODES

from apistar import Settings, commands, exceptions, http
from apistar.components import (
    commandline, console, dependency, router, schema, sessions, statics,
    templates, wsgi
)
from apistar.core import Command, Component
from apistar.frameworks.cli import CliApp
from apistar.interfaces import (
    Auth, CommandLineClient, Console, FileWrapper, Injector, Router, Schema,
    SessionStore, StaticFiles, Templates
)
from apistar.renderers import DEFAULT_RENDERERS, negotiate_renderer
from apistar.types import Handler, KeywordArgs, ReturnValue, WSGIEnviron

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
        Component(Console, init=console.PrintConsole),
        Component(SessionStore, init=sessions.LocalMemorySessionStore),
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
        Component(http.RequestStream, init=wsgi.get_stream),
        Component(http.RequestData, init=wsgi.get_request_data),
        Component(FileWrapper, init=wsgi.get_file_wrapper),
        Component(http.Session, init=sessions.get_session),
        Component(Auth, init=wsgi.get_auth)
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
                Handler: 'handler',
                KeywordArgs: 'kwargs',
                Exception: 'exc',
                http.ResponseHeaders: 'response_headers'
            },
            resolvers=[dependency.HTTPResolver()]
        )

    def __call__(self,
                 environ: typing.Dict[str, typing.Any],
                 start_response: typing.Callable):
        headers = http.ResponseHeaders()
        state = {
            'wsgi_environ': environ,
            'handler': None,
            'kwargs': None,
            'exc': None,
            'response_headers': headers
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']
        try:
            handler, kwargs = self.router.lookup(path, method)
            state['handler'], state['kwargs'] = handler, kwargs
            funcs = [self.check_permissions, handler, self.render_response]
            response = self.http_injector.run_all(funcs, state=state)
        except Exception as exc:
            state['exc'] = exc  # type: ignore
            funcs = [self.exception_handler, self.render_response]
            response = self.http_injector.run_all(funcs, state=state)

        # Get the WSGI response information, given the Response instance.
        try:
            status_text = STATUS_TEXT[response.status]
        except KeyError:
            status_text = str(response.status)

        headers.update(response.headers)
        if response.content_type is not None:
            headers['content-type'] = response.content_type

        if isinstance(response.content, (bytes, str)):
            content = [response.content]
        else:
            content = response.content

        # Return the WSGI response.
        start_response(status_text, list(headers))
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

    def check_permissions(self,
                          handler: Handler,
                          injector: Injector,
                          settings: Settings) -> None:
        default_permissions = settings.get('PERMISSIONS', None)
        permissions = getattr(handler, 'permissions', default_permissions)
        if permissions is None:
            return

        for permission in permissions:
            if not injector.run(permission.has_permission):
                raise exceptions.Forbidden()

    def render_response(self,
                        handler: Handler,
                        settings: Settings,
                        accept: http.Header,
                        ret: ReturnValue) -> http.Response:
        if isinstance(ret, http.Response):
            data, status, headers, content_type = ret
            if content_type is not None:
                return ret
        else:
            data, status, headers, content_type = ret, 200, {}, None

        if data is None:
            content = b''
            content_type = None
        else:
            default_renderers = settings.get('RENDERERS', DEFAULT_RENDERERS)
            renderers = getattr(handler, 'renderers', default_renderers)
            renderer = negotiate_renderer(accept, renderers)
            if renderer is None:
                raise exceptions.NotAcceptable()
            content = renderer.render(data)
            content_type = renderer.get_content_type()

        if not content and status == 200:
            status = 204
            content_type = None

        return http.Response(content, status, headers, content_type)
