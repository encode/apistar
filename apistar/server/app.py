import werkzeug

from apistar import exceptions
from apistar.http import (
    RESPONSE_STATUS_TEXT, HTMLResponse, JSONResponse, PathParams, Response
)
from apistar.server.core import Route, generate_document
from apistar.server.injector import Injector
from apistar.server.router import Router
from apistar.server.staticfiles import StaticFiles
from apistar.server.templates import Templates
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.wsgi import WSGI_COMPONENTS, WSGIEnviron, WSGIStartResponse


def exception_handler(exc: Exception):
    if isinstance(exc, exceptions.HTTPException):
        return JSONResponse(exc.detail, exc.status_code, exc.get_headers())
    raise


def render_response(response):
    if isinstance(response, Response):
        return response
    elif isinstance(response, str):
        return HTMLResponse(response)
    return JSONResponse(response)


def finalize_wsgi(response, start_response: WSGIStartResponse):
    start_response(
        RESPONSE_STATUS_TEXT[response.status_code],
        list(response.headers)
    )
    return [response.content]


class App():
    def __init__(self,
                 routes,
                 template_dir=None,
                 template_packages=None,
                 static_dir=None,
                 static_packages=None,
                 schema_url=None,
                 static_url=None,
                 components=None,
                 run_before_handler=None,
                 run_after_handler=None,
                 run_on_exception=None):
        routes = routes + self.include_extra_routes(schema_url, static_url)
        self.init_document(routes)
        self.init_router(routes)
        self.init_templates(template_dir, template_packages)
        self.init_staticfiles(static_url, static_dir, static_packages)
        self.init_injector(components)
        self.init_hooks(run_before_handler, run_after_handler, run_on_exception)

    def include_extra_routes(self, schema_url=None, static_url=None):
        extra_routes = []

        from apistar.server.handlers import serve_schema, serve_static

        if schema_url:
            extra_routes += [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]
        if static_url:
            static_url = static_url.rstrip('/') + '/{+filename}'
            extra_routes += [
                Route(static_url, method='GET', handler=serve_static, documented=False, standalone=True)
            ]
        return extra_routes

    def init_document(self, routes):
        self.document = generate_document(routes)

    def init_router(self, routes):
        self.router = Router(routes)

    def init_templates(self, template_dir: str=None, template_packages: list=None):
        template_globals = {'reverse_url': self.reverse_url}
        self.templates = Templates(template_dir, template_packages, template_globals)

    def init_staticfiles(self, static_url: str, static_dir: str=None, static_packages: list=None):
        self.statics = StaticFiles(static_url, static_dir, static_packages)

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

    def init_hooks(self, run_before_handler=None, run_after_handler=None, run_on_exception=None):
        if run_before_handler is None:
            self.run_before_handler = []
        else:
            self.run_before_handler = list(run_before_handler)

        if run_after_handler is None:
            self.run_after_handler = [render_response, finalize_wsgi]
        else:
            self.run_after_handler = list(run_after_handler) + [render_response, finalize_wsgi]

        if run_on_exception is None:
            self.run_on_exception = [exception_handler, finalize_wsgi]
        else:
            self.run_on_exception = list(run_on_exception) + [exception_handler, finalize_wsgi]

    def reverse_url(self, name: str, **params):
        return self.router.reverse_url(name, **params)

    def render_template(self, path: str, **context):
        return self.templates.render_template(path, **context)

    def serve(self, host, port, use_debugger=False):
        werkzeug.run_simple(host, port, self, use_debugger=use_debugger)

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
                    self.run_before_handler +
                    [route.handler] +
                    self.run_after_handler
                )
            return self.injector.run(funcs, state)
        except Exception as exc:
            state['exc'] = exc
            funcs = self.run_on_exception
            return self.injector.run(funcs, state)
