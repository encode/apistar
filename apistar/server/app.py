import json

from werkzeug.http import HTTP_STATUS_CODES

from apistar import exceptions
from apistar.server import http
from apistar.server.injector import Injector
from apistar.server.router import Router
from apistar.server.templates import TemplateRenderer
from apistar.server.wsgi import WSGI_COMPONENTS, WSGIEnviron

STATUS_TEXT = {
    code: "%d %s" % (code, msg)
    for code, msg in HTTP_STATUS_CODES.items()
}


def exception_handler(exc: Exception) -> http.Response:
    if isinstance(exc, exceptions.HTTPException):
        return http.Response(exc.detail, exc.status_code, exc.get_headers())
    raise


class App():
    components = WSGI_COMPONENTS

    def __init__(self, document):
        self.document = document
        self.router = self.get_router()
        self.template_renderer = self.get_template_renderer()
        self.injector = self.get_injector()
        self.exception_handler = exception_handler

    def get_initial_components(self):
        return {
            'environ': WSGIEnviron,
            'exc': Exception,
            'app': App
        }

    def get_router(self):
        return Router(self.document)

    def get_template_renderer(self):
        return TemplateRenderer(self)

    def get_injector(self):
        initial_components = self.get_initial_components()
        return Injector(self.components, initial_components)

    def reverse_url(self, name: str, params: dict=None):
        return self.router.reverse_url(name, params)

    def render_template(self, path: str, **context):
        return self.template_renderer.render_template(path, **context)

    def static_url(self, path: str):
        return '#'

    def __call__(self, environ, start_response):
        state = {
            'environ': environ,
            'exc': None,
            'app': self
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']
        try:
            link, handler, path_kwargs = self.router.lookup(path, method)
            # state['link'], state['handler'], state['path_kwargs'] = link, handler, path_kwargs
            response = self.injector.run(handler, state)
        except Exception as exc:
            state['exc'] = exc
            response = self.injector.run(self.exception_handler, state)

        # Get the WSGI response information, given the Response instance.
        try:
            status_text = STATUS_TEXT[response.status]
        except KeyError:
            status_text = str(response.status)

        if isinstance(response.content, str):
            content = [response.content.encode('utf-8')]
        elif isinstance(response.content, bytes):
            content = [response.content]
        else:
            content = [json.dumps(response.content).encode('utf-8')]

        # Return the WSGI response.
        start_response(status_text, list(response.headers))
        return content
