import sys
import typing

import werkzeug

from apistar import exceptions
from apistar.http import HTMLResponse, JSONResponse, PathParams, Response
from apistar.server.adapters import ASGItoWSGIAdapter
from apistar.server.asgi import (
    ASGI_COMPONENTS, ASGIReceive, ASGIScope, ASGISend
)
from apistar.server.components import Component, ReturnValue
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
                 packages=None,
                 schema_url='/schema/',
                 docs_url='/docs/',
                 static_url='/static/',
                 components=None,
                 event_hooks=None):

        packages = tuple() if packages is None else tuple(packages)

        if docs_url is not None:
            packages += ('apistar',)

        if static_dir is None and not packages:
            static_url = None

        # Guard against some easy misconfiguration.
        if components:
            msg = 'components must be a list of instances of Component.'
            assert all([isinstance(component, Component) for component in components]), msg
        if event_hooks:
            msg = 'event_hooks must be a list.'
            assert isinstance(event_hooks, (list, tuple)), msg

        routes = routes + self.include_extra_routes(schema_url, docs_url, static_url)
        self.init_document(routes)
        self.init_router(routes)
        self.init_templates(template_dir, packages)
        self.init_staticfiles(static_url, static_dir, packages)
        self.init_injector(components)
        self.debug = False
        self.event_hooks = event_hooks

        # Ensure event hooks can all be instantiated.
        self.get_event_hooks()

    def include_extra_routes(self, schema_url=None, docs_url=None, static_url=None):
        extra_routes = []

        from apistar.server.handlers import serve_documentation, serve_schema, serve_static_wsgi

        if schema_url:
            extra_routes += [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]
        if docs_url:
            extra_routes += [
                Route(docs_url, method='GET', handler=serve_documentation, documented=False)
            ]
        if static_url:
            static_url = static_url.rstrip('/') + '/{+filename}'
            extra_routes += [
                Route(
                    static_url, method='GET', handler=serve_static_wsgi,
                    name='static', documented=False, standalone=True
                )
            ]
        return extra_routes

    def init_document(self, routes):
        self.document = generate_document(routes)

    def init_router(self, routes):
        self.router = Router(routes)

    def init_templates(self, template_dir: str=None, packages: typing.Sequence[str]=None):
        if not template_dir and not packages:
            self.templates = None
        else:
            template_globals = {
                'reverse_url': self.reverse_url,
                'static_url': self.static_url
            }
            self.templates = Templates(template_dir, packages, template_globals)

    def init_staticfiles(self, static_url: str, static_dir: str=None, packages: typing.Sequence[str]=None):
        if not static_dir and not packages:
            self.statics = None
        else:
            self.statics = StaticFiles(static_url, static_dir, packages)

    def init_injector(self, components=None):
        components = components if components else []
        components = list(WSGI_COMPONENTS + VALIDATION_COMPONENTS) + components
        initial_components = {
            'environ': WSGIEnviron,
            'start_response': WSGIStartResponse,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'route': Route,
            'response': Response
        }
        self.injector = Injector(components, initial_components)

    def get_event_hooks(self):
        event_hooks = []
        for hook in self.event_hooks or []:
            if isinstance(hook, type):
                # New style usage, instantiate hooks on requests.
                event_hooks.append(hook())
            else:
                # Old style usage, to be deprecated on the next version bump.
                event_hooks.append(hook)

        on_request = [
            hook.on_request for hook in event_hooks
            if hasattr(hook, 'on_request')
        ]

        on_response = [
            hook.on_response for hook in reversed(event_hooks)
            if hasattr(hook, 'on_response')
        ]

        on_error = [
            hook.on_error for hook in reversed(event_hooks)
            if hasattr(hook, 'on_error')
        ]

        return on_request, on_response, on_error

    def static_url(self, filename):
        return self.router.reverse_url('static', filename=filename)

    def reverse_url(self, name: str, **params):
        return self.router.reverse_url(name, **params)

    def render_template(self, path: str, **context):
        return self.templates.render_template(path, **context)

    def serve(self, host, port, debug=False, **options):
        self.debug = debug
        if 'use_debugger' not in options:
            options['use_debugger'] = debug
        if 'use_reloader' not in options:
            options['use_reloader'] = debug
        werkzeug.run_simple(host, port, self, **options)

    def render_response(self, return_value: ReturnValue) -> Response:
        if isinstance(return_value, Response):
            return return_value
        elif isinstance(return_value, str):
            return HTMLResponse(return_value)
        return JSONResponse(return_value)

    def exception_handler(self, exc: Exception) -> Response:
        if isinstance(exc, exceptions.HTTPException):
            return JSONResponse(exc.detail, exc.status_code, exc.get_headers())
        raise

    def error_handler(self) -> Response:
        return JSONResponse('Server error', 500, exc_info=sys.exc_info())

    def finalize_wsgi(self, response: Response, start_response: WSGIStartResponse):
        if self.debug and response.exc_info is not None:
            exc_info = response.exc_info
            raise exc_info[0].with_traceback(exc_info[1], exc_info[2])

        start_response(
            RESPONSE_STATUS_TEXT[response.status_code],
            list(response.headers),
            response.exc_info
        )
        return [response.content]

    def __call__(self, environ, start_response):
        state = {
            'environ': environ,
            'start_response': start_response,
            'exc': None,
            'app': self,
            'path_params': None,
            'route': None,
            'response': None,
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']

        if self.event_hooks is None:
            on_request, on_response, on_error = [], [], []
        else:
            on_request, on_response, on_error = self.get_event_hooks()

        try:
            route, path_params = self.router.lookup(path, method)
            state['route'] = route
            state['path_params'] = path_params
            if route.standalone:
                funcs = [route.handler]
            else:
                funcs = (
                    on_request +
                    [route.handler, self.render_response] +
                    on_response +
                    [self.finalize_wsgi]
                )
            return self.injector.run(funcs, state)
        except Exception as exc:
            try:
                state['exc'] = exc
                funcs = (
                    [self.exception_handler] +
                    on_response +
                    [self.finalize_wsgi]
                )
                return self.injector.run(funcs, state)
            except Exception as inner_exc:
                try:
                    state['exc'] = inner_exc
                    self.injector.run(on_error, state)
                finally:
                    funcs = [self.error_handler, self.finalize_wsgi]
                    return self.injector.run(funcs, state)


class ASyncApp(App):
    interface = 'asgi'

    def include_extra_routes(self, schema_url=None, docs_url=None, static_url=None):
        extra_routes = []

        from apistar.server.handlers import serve_documentation, serve_schema, serve_static_asgi

        if schema_url:
            extra_routes += [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]
        if docs_url:
            extra_routes += [
                Route(docs_url, method='GET', handler=serve_documentation, documented=False)
            ]
        if static_url:
            static_url = static_url.rstrip('/') + '/{+filename}'
            extra_routes += [
                Route(
                    static_url, method='GET', handler=serve_static_asgi,
                    name='static', documented=False, standalone=True
                )
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
            'route': Route,
            'response': Response,
        }
        self.injector = ASyncInjector(components, initial_components)

    def init_staticfiles(self, static_url: str, static_dir: str=None, packages: typing.Sequence[str]=None):
        if not static_dir and not packages:
            self.statics = None
        else:
            self.statics = ASyncStaticFiles(static_url, static_dir, packages)

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

            if self.event_hooks is None:
                on_request, on_response, on_error = [], [], []
            else:
                on_request, on_response, on_error = self.get_event_hooks()

            try:
                route, path_params = self.router.lookup(path, method)
                state['route'] = route
                state['path_params'] = path_params
                if route.standalone:
                    funcs = [route.handler]
                else:
                    funcs = (
                        on_request +
                        [route.handler, self.render_response] +
                        on_response +
                        [self.finalize_asgi]
                    )
                await self.injector.run_async(funcs, state)
            except Exception as exc:
                try:
                    state['exc'] = exc
                    funcs = (
                        [self.exception_handler] +
                        on_response +
                        [self.finalize_asgi]
                    )
                    await self.injector.run_async(funcs, state)
                except Exception as inner_exc:
                    try:
                        state['exc'] = inner_exc
                        await self.injector.run_async(on_error, state)
                    finally:
                        funcs = [self.error_handler, self.finalize_asgi]
                        await self.injector.run_async(funcs, state)
        return asgi_callable

    async def finalize_asgi(self, response: Response, send: ASGISend, scope: ASGIScope):
        if response.exc_info is not None:
            if self.debug or scope.get('raise_exceptions', False):
                exc_info = response.exc_info
                raise exc_info[0].with_traceback(exc_info[1], exc_info[2])

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

    def serve(self, host, port, debug=False, **options):
        self.debug = debug
        if 'use_debugger' not in options:
            options['use_debugger'] = debug
        if 'use_reloader' not in options:
            options['use_reloader'] = debug
        wsgi = ASGItoWSGIAdapter(self, raise_exceptions=debug)
        werkzeug.run_simple(host, port, wsgi, **options)
