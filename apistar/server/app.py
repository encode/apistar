import werkzeug

from apistar import exceptions
from apistar.http import (
    RESPONSE_STATUS_TEXT, HTMLResponse, JSONResponse, PathParams, Response
)
from apistar.server.core import Route, generate_document
from apistar.server.injector import Injector
from apistar.server.router import Router
from apistar.server.templates import Templates
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.wsgi import WSGI_COMPONENTS, WSGIEnviron


def exception_handler(exc: Exception):
    if isinstance(exc, exceptions.HTTPException):
        return JSONResponse(exc.detail, exc.status_code, exc.get_headers())
    raise


class App():
    def __init__(self, routes, template_dir=None, template_apps=None, components=None, schema_url=None):
        components = list(components) if components else []

        if schema_url is not None:
            from apistar.server.handlers import serve_schema
            routes = routes + [
                Route(schema_url, method='GET', handler=serve_schema, documented=False)
            ]

        self.document = generate_document(routes)
        self.router = self.init_router(routes)
        self.templates = self.init_templates(template_dir, template_apps)
        self.injector = self.init_injector(components)
        self.exception_handler = exception_handler

    def init_router(self, routes):
        return Router(routes)

    def init_templates(self, template_dir: str=None, template_apps: list=None):
        return Templates(template_dir, template_apps, {
            'reverse_url': self.reverse_url,
            'static_url': self.static_url
        })

    def init_injector(self, components=None):
        components = components if components else []
        components = list(WSGI_COMPONENTS + VALIDATION_COMPONENTS) + components
        initial_components = {
            'environ': WSGIEnviron,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'route': Route
        }
        return Injector(components, initial_components)

    def reverse_url(self, name: str, **params):
        return self.router.reverse_url(name, **params)

    def render_template(self, path: str, **context):
        return self.templates.render_template(path, **context)

    def static_url(self, path: str):
        return '#'

    def render_response(self, data):
        if isinstance(data, str):
            return HTMLResponse(data)
        return JSONResponse(data)

    def serve(self, host, port, use_debugger=False, **kwargs):
        werkzeug.run_simple(host, port, self, use_debugger=use_debugger, **kwargs)

    def __call__(self, environ, start_response):
        state = {
            'environ': environ,
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
            response = self.injector.run(route.handler, state)
        except Exception as exc:
            state['exc'] = exc
            response = self.injector.run(self.exception_handler, state)

        if not isinstance(response, Response):
            response = self.render_response(response)

        # Return the WSGI response.
        start_response(
            RESPONSE_STATUS_TEXT[response.status_code],
            list(response.headers)
        )
        return [response.content]
