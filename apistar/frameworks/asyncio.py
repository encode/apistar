import json
import typing

from apistar import commands, exceptions, http
from apistar.cli import Command
from apistar.components import (
    commandline, console, dependency, router, schema, statics, templates, umi
)
from apistar.frameworks.cli import CliApp
from apistar.interfaces import (
    CommandLineClient, Console, Injector, KeywordArgs, Router, Schema,
    StaticFiles, Templates, UMIChannels, UMIMessage
)


class ASyncIOApp(CliApp):
    INJECTOR_CLS = dependency.AsyncDependencyInjector

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
        http.Method: umi.get_method,
        http.URL: umi.get_url,
        http.Scheme: umi.get_scheme,
        http.Host: umi.get_host,
        http.Port: umi.get_port,
        http.Path: umi.get_path,
        http.Headers: umi.get_headers,
        http.Header: umi.get_header,
        http.QueryString: umi.get_querystring,
        http.QueryParams: umi.get_queryparams,
        http.QueryParam: umi.get_queryparam,
        http.Body: umi.get_body,
        # http.RequestData: umi.get_request_data,
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
                UMIMessage: 'message',
                UMIChannels: 'channels',
                KeywordArgs: 'kwargs',
                Exception: 'exc'
            },
            resolvers=[dependency.HTTPResolver()]
        )

    async def __call__(self,
                       message: typing.Dict[str, typing.Any],
                       channels: typing.Dict[str, typing.Any]):
        state = {
            'message': message,
            'channels': channels,
            'kwargs': None,
            'exc': None
        }
        method = message['method'].upper()
        path = message['path']
        try:
            handler, kwargs = self.router.lookup(path, method)
            state['kwargs'] = kwargs
            response = await self.http_injector.run_async(handler, state=state)
        except Exception as exc:
            state['exc'] = exc  # type: ignore
            response = await self.http_injector.run_async(self.exception_handler, state=state)

        if getattr(response, 'content_type', None) is None:
            response = self.finalize_response(response)

        response_message = {
            'status': response.status,
            'headers': [
                [key.encode(), value.encode()]
                for key, value in response.headers.items()
            ] + [
                [b'content-type', response.content_type.encode()]
            ],
            'content': response.content
        }
        await channels['reply'].send(response_message)

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
