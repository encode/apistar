import werkzeug

from apistar import exceptions
from apistar.http import HTMLResponse, JSONResponse, PathParams, Response
from apistar.server.adapters import ASGItoWSGIAdapter
from apistar.server.asgi import (
    ASGI_COMPONENTS, ASGIReceive, ASGIScope, ASGISend
)
from apistar.server.components import Component
from apistar.server.core import Route, generate_document
from apistar.server.injector import ASyncInjector, Injector
from apistar.server.router import Router
from apistar.server.staticfiles import ASyncStaticFiles, StaticFiles
from apistar.server.templates import Templates
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.wsgi import (
    RESPONSE_STATUS_TEXT, WSGI_COMPONENTS, WSGIEnviron, WSGIStartResponse
)


class App():
    interface = 'wsgi'

    def __init__(self,
                 routes,
                 template_dir=None,
                 static_dir=None,
                 schema_url='/schema/',
                 static_url='/static/',
                 components=None,
                 event_hooks=None):

        if static_dir is None:
            static_url = None

        # Guard against some easy misconfiguration.
        if components:
            msg = 'components must be a list of instances of Component.'
            assert all([isinstance(component, Component) for component in components]), msg
        if event_hooks:
            msg = 'event_hooks must be a list of instances, not classes.'
            assert not any([isinstance(event_hook, type) for event_hook in event_hooks]), msg

        routes = routes + self.include_extra_routes(schema_url, static_url)
        self.init_document(routes)
        self.init_router(routes)
        self.init_templates(template_dir)
        self.init_staticfiles(static_url, static_dir)
        self.init_injector(components)
        self.init_hooks(event_hooks)

    def include_extra_routes(self, schema_url=None, static_url=None):
        extra_routes = []

        from apistar.server.handlers import serve_schema, serve_static_wsgi

        if schema_url:
            extra_routes += [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]
        if static_url:
            static_url = static_url.rstrip('/') + '/{+filename}'
            extra_routes += [
                Route(static_url, method='GET', handler=serve_static_wsgi, documented=False, standalone=True)
            ]
        return extra_routes

    def init_document(self, routes):
        self.document = generate_document(routes)

    def init_router(self, routes):
        self.router = Router(routes)

    def init_templates(self, template_dir: str=None):
        if not template_dir:
            self.templates = None
        else:
            template_globals = {'reverse_url': self.reverse_url}
            self.templates = Templates(template_dir, template_globals)

    def init_staticfiles(self, static_url: str, static_dir: str=None):
        if not static_dir:
            self.statics = None
        else:
            self.statics = StaticFiles(static_url, static_dir)

    def init_injector(self, components=None):
        components = components if components else []
        components = list(WSGI_COMPONENTS + VALIDATION_COMPONENTS) + components
        initial_components = {
            'environ': WSGIEnviron,
            'start_response': WSGIStartResponse,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'route': Route
        }
        self.injector = Injector(components, initial_components)

    def init_hooks(self, event_hooks=None):
        if event_hooks is None:
            event_hooks = []

        self.on_request_functions = [
            hook.on_request for hook in event_hooks
            if hasattr(hook, 'on_request')
        ]

        self.on_response_functions = [self.render_response] + [
            hook.on_response for hook in event_hooks
            if hasattr(hook, 'on_response')
        ] + [self.finalize_wsgi]

        self.on_error_functions = [self.exception_handler] + [
            hook.on_error for hook in event_hooks
            if hasattr(hook, 'on_error')
        ] + [self.finalize_wsgi]

    def reverse_url(self, name: str, **params):
        return self.router.reverse_url(name, **params)

    def render_template(self, path: str, **context):
        return self.templates.render_template(path, **context)

    def serve(self, host, port, **options):
        werkzeug.run_simple(host, port, self, **options)

    def render_response(self, response):
        if isinstance(response, Response):
            return response
        elif isinstance(response, str):
            return HTMLResponse(response)
        return JSONResponse(response)

    def finalize_wsgi(self, response, start_response: WSGIStartResponse):
        start_response(
            RESPONSE_STATUS_TEXT[response.status_code],
            list(response.headers)
        )
        return [response.content]

    def exception_handler(self, exc: Exception):
        if isinstance(exc, exceptions.HTTPException):
            return JSONResponse(exc.detail, exc.status_code, exc.get_headers())
        raise

    def __call__(self, environ, start_response):
        state = {
            'environ': environ,
            'start_response': start_response,
            'exc': None,
            'app': self,
            'path_params': None,
            'route': None
        }

        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']

        try:
            route, path_params = self.router.lookup(path, method)
            state['route'] = route
            state['path_params'] = path_params

            if route.standalone:
                funcs = [route.handler]
            else:
                funcs = (
                    self.on_request_functions +
                    [route.handler] +
                    self.on_response_functions
                )

            return self.injector.run(funcs, state)
        except Exception as exc:
            state['exc'] = exc
            funcs = self.on_error_functions
            return self.injector.run(funcs, state)


class ASyncApp(App):
    interface = 'asgi'

    def include_extra_routes(self, schema_url=None, static_url=None):
        extra_routes = []

        from apistar.server.handlers import serve_schema, serve_static_asgi

        if schema_url:
            extra_routes += [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]

        if static_url:
            static_url = static_url.rstrip('/') + '/{+filename}'
            extra_routes += [
                Route(static_url, method='GET', handler=serve_static_asgi, documented=False, standalone=True)
            ]
        return extra_routes

    def init_injector(self, components=None):
        components = components if components else []
        components = list(ASGI_COMPONENTS + VALIDATION_COMPONENTS) + components
        initial_components = {
            'scope': ASGIScope,
            'receive': ASGIReceive,
            'send': ASGISend,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'route': Route
        }
        self.injector = ASyncInjector(components, initial_components)

    def init_hooks(self, event_hooks=None):
        if event_hooks is None:
            event_hooks = []

        self.on_request_functions = [
            hook.on_request for hook in event_hooks
            if hasattr(hook, 'on_request')
        ]

        self.on_response_functions = [self.render_response] + [
            hook.on_response for hook in event_hooks
            if hasattr(hook, 'on_response')
        ] + [self.finalize_asgi]

        self.on_error_functions = [self.exception_handler] + [
            hook.on_error for hook in event_hooks
            if hasattr(hook, 'on_error')
        ] + [self.finalize_asgi]

    def init_staticfiles(self, static_url: str, static_dir: str=None):
        if not static_dir:
            self.statics = None
        else:
            self.statics = ASyncStaticFiles(static_url, static_dir)

    def __call__(self, scope):
        async def asgi_callable(receive, send):
            state = {
                'scope': scope,
                'receive': receive,
                'send': send,
                'exc': None,
                'app': self,
                'path_params': None,
                'route': None
            }

            method = scope['method']
            path = scope['path']

            try:
                route, path_params = self.router.lookup(path, method)
                state['route'] = route
                state['path_params'] = path_params
                if route.standalone:
                    funcs = [route.handler]
                else:
                    funcs = (
                        self.on_request_functions +
                        [route.handler] +
                        self.on_response_functions
                    )
                await self.injector.run_async(funcs, state)
            except Exception as exc:
                state['exc'] = exc
                funcs = self.on_error_functions
                await self.injector.run_async(funcs, state)
        return asgi_callable

    async def finalize_asgi(self, response, send: ASGISend):
        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': [
                [key.encode(), value.encode()]
                for key, value in response.headers
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': response.content
        })

    def serve(self, host, port, **options):
        wsgi = ASGItoWSGIAdapter(self)
        werkzeug.run_simple(host, port, wsgi, **options)
